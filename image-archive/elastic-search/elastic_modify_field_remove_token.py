# Usage:
# source ./image-archive/environments/local/env.sh
# python3 elastic_associate_reports_with_images.py

import re
import os
import sys
import json
import time
import pydicom

from elasticsearch import Elasticsearch
from IPython import embed


ELASTIC_IP = os.environ['ELASTIC_IP']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
DICOM_BASE_PATH = '../reactive-search/'


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

    # Prefix key with 'rr' which stands for radiology report
    key = "rr" + key

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
      "_source": ["_id",'dicom_relativepath', 'thumbnail_filepath'],
      'query': {'match_all': {}}}
    )
    dicom_filepaths = [hit['_source']['dicom_filepath'] for hit in results['hits']['hits']]

    if dicom_filepaths == []:
      print('Nothing found for AccessionNumber')

    # Add report info to metadata in dicom on disk
    update_dicoms(report, dicom_filepaths)

if __name__ == '__main__':
  from_index_name = 'report'
  to_index_name = 'image'

  # Define config
  scroll_size = 5000
  search_body = {
    # All Fields
    # "_source":[field] # Select only one field instead of all
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
    scroll='2m',
    size=scroll_size,
    body=search_body
  )

  # Get the scroll ID
  sid = data['_scroll_id']
  scroll_size = len(data['hits']['hits'])

  # Before scroll, process current batch of hits
  process_hits(data['hits']['hits'])

  t0 = time.time()
  hit_count = data['hits']['total']

  while scroll_size > 0:
    data = es.scroll(scroll_id=sid, scroll='2m')

    # Process current batch of hits
    process_hits(data['hits']['hits'])

    # Update the scroll ID
    sid = data['_scroll_id']

    # Get the number of results that returned in the last scroll
    scroll_size = len(data['hits']['hits'])

  elapsed_time = time.time() - t0
  dl_rate = hit_count / elapsed_time
  print('\n{} documents updated in Elastic Search '.format(hit_count) + 'in {:.2f} seconds.'.format(elapsed_time), file=sys.stderr)
  print('Update rate (documents/s): {:.2f}'.format(dl_rate), file=sys.stderr)
