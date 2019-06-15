## Usage:
# source ../environments/local/env.sh
# python3 elastic_associate_reports_with_images.py  --input_range 0-4
#
# qlogin #Specific to HPF
# source ./image-archive/environments/local/env.sh
# export ELASTIC_IP='192.168.100.61' #Specific to HPF
# python3 ./image-archive/elastic-search/elastic_associate_reports_with_images.py  --input_range 0-4


import re
import os
import sys
import json
import time
import pydicom
import logging
import argparse
import traceback

from elasticsearch import Elasticsearch
from IPython import embed

logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
                    # level=logging.DEBUG)
log = logging.getLogger('main')


ELASTIC_IP = os.environ['ELASTIC_IP']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
DICOM_BASE_PATH = os.environ.get('DICOM_BASE_PATH','../reactive-search/')

def update_dicoms(report, dicom_filepaths):
  """Add report info to metadata in dicom on disk"""
  # TODO: check for unused group
  # TODO: check for unused key
  if not report:
    return

  # Loop over images. There may be multiple images related to the report
  for filepath in dicom_filepaths:
    filepath = os.path.join(DICOM_BASE_PATH, filepath)
    dicom = pydicom.dcmread(filepath)
    dicom_datatype = 'LT' # Dicom datatype Value Representation "LT" is for Long Text with 10240 chars maximum
    loc_group = 0x0019
    loc_element = 0x0030

    # Add new data in dicom metadata
    for key, value in report.items():
      # Remove all non-word characters (everything except numbers and letters)
      key = re.sub(r"[^\w\s]", '', key)
      key = re.sub(r"\s+", '', key)
      loc = (loc_group, loc_element)
      if loc in dicom:
        # log.warning('This DICM already has a value at position %s=%s' % (loc, str(dicom[loc])[0:100]))
        pass
      value = "Report %s: %s" % (key, str(value)) # Append key name to start of value because dicom uses hexadecimal instead of key names
      log.debug('Inserting Value: %s' % value)
      dicom[loc] = pydicom.DataElement(loc, dicom_datatype, value)
      loc_element = loc_element + 1 # increment to use higher index on next loop

    # Save updated dicom
    dicom.save_as(filepath)
    log.info('Saved DICOM: %s' % filepath)


def make_update_script_from_report(report):
  """ The main purpose is to create a script (in elasticsearch script format) that will add fields, but ignore a few blacklisted field names that are probably redundant or overlapping 

  Adding one new field looks like this:
    'script': {"inline": "ctx._source.A_new_attribute = 'NEWVALUE'"}}

  Multiple new fields are seperated by semicolons;
    'script': {"inline": "ctx._source.A_new_attribute = 'NEWVALUE'; ctx._source.A_second_attribute = 'SECOND'"}}
  """
  update_script = ""

  for key, value in report.items():
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

  return update_script

# Process hits here
def process_hits(hits):
  for item in hits:
    report = item['_source']
    AccessionNumber = report['Accession Number']
    log.info("\nProcessing AccessionNumber: %s" % AccessionNumber)

    update = make_update_script_from_report(report)

    # Insert report information into image in ElasticSearch documents that match AccessionNumber.
    # https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.update_by_query
    result = es.update_by_query(index=to_index_name, doc_type=to_index_name, body={
      'query': {'term': {'AccessionNumber.keyword': AccessionNumber}},
      'script': {"inline": update}}
    )
    if result['total'] == 0:
      log.info('Nothing found for AccessionNumber')
      continue

    log.info('Inserting report data into ElasticSearch %s documents. Full response: %s' % (result['total'], result))

    # Get filepaths of the images that we just updated.
    # NOTE: this code block can be removed after this issue is resolved
    # https://github.com/elastic/elasticsearch-py/issues/783
    results = es.search(index=to_index_name, doc_type=to_index_name, body={
      "_source": ["_id",'dicom_filepath'],
      'query': {'term': {'AccessionNumber.keyword': AccessionNumber}}}
    )
    dicom_filepaths = [hit['_source']['dicom_filepath'] for hit in results['hits']['hits']]


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
  size = input_end - input_start + 1
  search_body = {

  }

  # Init Elasticsearch instance
  es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])

  # Check index exists
  if not es.indices.exists(index=from_index_name):
    log.info("Index " + from_index_name + " not exists")
    exit()

  # Init scroll by search
  data = es.search(
    index=from_index_name,
    doc_type=from_index_name,
    from_=input_start, #the first report is at 0
    size=size,
    body=search_body
  )

  t0 = time.time()
  count = 0

  try:
    process_hits(data['hits']['hits'])
  except:
    log.error(traceback.format_exc())
    log.error('Skipping this image because of unknown error ^')

  elapsed_time = time.time() - t0
  dl_rate = count / elapsed_time
  log.info('\n{} images were updated in Elastic Search '.format(count) + 'in {:.2f} seconds.'.format(elapsed_time))
  log.info('Update rate (documents/s): {:.2f}'.format(dl_rate))
  
