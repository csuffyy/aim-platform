# Usage:
  #qlogin #Specific to HPF
  #source ./image-archive/environments/local/env.sh
  #export ELASTIC_IP='192.168.100.61' #Specific to HPF
  #python3 ./image-archive/elastic-search/elastic_associate_reports_with_images.py  --input_range 0-4

import re
import os
import sys
import json
import time
import pydicom
import argparse

from elasticsearch import Elasticsearch
from IPython import embed


ELASTIC_IP = os.environ['ELASTIC_IP']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
DICOM_BASE_PATH = '../reactive-search/'

def update_dicoms(report, dicom_filepaths):
  """Add report info to metadata in dicom on disk"""
  # TODO: check for unused group
  # TODO: check for unused key

  # Loop over images. There may be multiple images related to the report
  for filepath in dicom_filepaths:
    filepath = os.path.join(DICOM_BASE_PATH, filepath)
    ds = pydicom.dcmread(filepath)
    dicom_datatype = 'LT' # Dicom datatype Value Representation
    loc_group = 0x0019
    loc_element = 0x0030

    # Add new data in dicom metadata
    for key, value in report.items():
      # Remove all non-word characters (everything except numbers and letters)
      key = re.sub(r"[^\w\s]", '', key)
      key = re.sub(r"\s+", '', key)
      loc = (loc_group, loc_element)
      value = "Report %s: %s" % (key, str(value)) # Append key name to start of value because dicom uses hexadecimal instead of key names
      # ds[loc] = pydicom.DataElement(loc, dicom_datatype, value)
      print('Inserting Value: %s' % value)
      ds[loc] = pydicom.DataElement(loc, dicom_datatype, value)
      # embed()
      # ds[0x0019, 0x0030] = pydicom.DataElement(0x00190030, 'LO', 'Assumed TransferSyntaxUID')
      loc_element = loc_element + 1 # increment to use higher index on next loop
      # break

    # Save updated dicom
    ds.save_as(filepath)
    print('Saved DICOM: %s' % filepath)


def make_update_script_from_report(report):
  """ The main purpose is to create a script (in elasticsearch script format) that will add fields, but ignore a few blacklisted field names that are probably redundant or overlapping 

  Adding one new field looks like this:
    'script': {"inline": "ctx._source.A_new_attribute = 'NEWVALUE'"}}

  Multiple new fields are seperated by semicolons;
    'script': {"inline": "ctx._source.A_new_attribute = 'NEWVALUE'; ctx._source.A_second_attribute = 'SECOND'"}}
  """
  update_script = ""

  for key, value in report.items():
    # NOTE: Commented section out because I am now prefixing field names with rr, so overlaps of field names are very unlikely now.
    # Skip blacklisted keys
    # # Skip anything with id in it. Study ID, PatientId, etc. These are too important to potentially overwrite
    # if key.lower().find('id') >= 0:
    #   continue
    # # Replace filepath with report_filepath so that it is more specific
    # if key == 'filepath':
    #   key = 'report_filepath'

    blacklist = ['original_title', 'searchallblank']
    if key in blacklist:
      continue

    # Remove all non-word characters (everything except numbers and letters)
    key = re.sub(r"[^\w\s]", '', key)
    key = re.sub(r"\s+", '', key)

    # Prefix key with 'Report' which stands for radiology report
    key = "Report" + key

    # Append the adding of a new new key value to update script
    update_script = update_script + "ctx._source.%s = '%s'; " % (key, value)

  # print(update_script)
  return update_script

# Process hits here
def process_hits(hits):
  for item in hits:
    report = item['_source']
    AccessionNumber = report['Accession Number']
    print("Processing AccessionNumber: %s" % AccessionNumber, file=sys.stderr, flush=True)

    update = make_update_script_from_report(report)

    # https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.update_by_query
    es.update_by_query(index=to_index_name, doc_type=to_index_name, body={
      'query': {'term': {'AccessionNumber.keyword': AccessionNumber}},
      'script': {"inline": update}}
    )

    # NOTE: this code block can be removed after this issue is resolved
    # https://github.com/elastic/elasticsearch-py/issues/783
    results = es.search(index=to_index_name, doc_type=to_index_name, body={
      "_source": ["_id",'dicom_filepath'],
      'query': {'term': {'AccessionNumber.keyword': AccessionNumber}}}
    )
    dicom_filepaths = [hit['_source']['dicom_filepath'] for hit in results['hits']['hits']]

    if dicom_filepaths == []:
      print('Nothing found for AccessionNumber')

    # Add report info to metadata in dicom on disk
    update_dicoms(report, dicom_filepaths)

    # Count number of images updated
    global count
    count = count + len(dicom_filepaths)


if __name__ == '__main__':
  from_index_name = 'report'
  to_index_name = 'image'

  # To get the range for the DICOM files to look for matches
  parser = argparse.ArgumentParser(description='Associates reports with the DICOM files already in ElasticSearch')
  parser.add_argument('--input_range', help='Positional document numbers in ElasticSearch (ex. 1-10). These documents will be processed.')
  args = parser.parse_args()
  input_range = args.input_range
  #log.info("Settings: %s=%s" % ('input_range', input_range))

  # Define config
  # To set the start and end of the range of DICOM files to look for matches in
  input_start, input_end = [int(i) for i in input_range.split('-')]
  search_body = {

  }

  # Init Elasticsearch instance
  es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])

  # Check index exists
  if not es.indices.exists(index=from_index_name):
    print("Index " + from_index_name + " not exists")
    exit()

  # Init scroll by search
  data = es.search(
    index=from_index_name,
    doc_type=from_index_name,
    from_=input_start, #the first report is at 0
    size=input_end,
    body=search_body
  )

  t0 = time.time()
  count = 0

  process_hits(data['hits']['hits'])

  elapsed_time = time.time() - t0
  dl_rate = count / elapsed_time
  print('\n{} images were updated in Elastic Search '.format(count) + 'in {:.2f} seconds.'.format(elapsed_time), file=sys.stderr)
  print('Update rate (documents/s): {:.2f}'.format(dl_rate), file=sys.stderr)
