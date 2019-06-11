#!/bin/python
#
# Usage:
# source ../environments/local/env.sh && python3 load_reports_elastic.py ../reports/sample/report_list

import os 
import glob
import random
import logging
import traceback
import argparse
import elasticsearch.exceptions
import time

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from datetime import datetime
from IPython import embed
from parse_all_colons import process_file

logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
                    # level=logging.DEBUG)
log = logging.getLogger('main')
    


def is_report_in_elastic(filepath):
  query = {
    "query" : {
      "term" : { "filepath.keyword" : filepath }
    },
    "_source": '_id'
  }
  res = es.search(index=INDEX_NAME, body=query)
  return res['hits']['total'] >= 1

def load_reports():
  for filepath in files:
    try:
      if not filepath:
        continue

      # If this report is already in Elastic, skip, don't add again
      # if is_report_in_elastic(filepath):
      #   log.info('Skipping because found in Elastic: %s' % filepath)
      #   continue

      # Load Report
      report = process_file(filepath)

      # Remove values that have keys that are longer than 30 characters
      long_keys = [key for key in report.keys() if len(key) > 30] # find long keys
      list(map(report.pop, long_keys)) # remove long keys from dict

      log.info('\nProcessing: %s' % filepath)
      report['original_title'] = 'Report'
      report['filepath'] = filepath
      report['_index'] = INDEX_NAME
      report['_type'] = DOC_TYPE
      report['searchallblank'] = '' # needed to search across everything (via searching for empty string)
      yield report
    except:
      print(traceback.format_exc())
      log.error('Skipping this report because of unknown error')
      # raise


if __name__ == '__main__':
  # Set up command line arguments
  parser = argparse.ArgumentParser(description='Load reports to Elastic.')
  parser.add_argument('input_filenames', help='File containing report file names.')
  parser.add_argument('-n', '--num', type=int, default=500, help='Bulk chunksize.')
  args = parser.parse_args()
  input_filenames = args.input_filenames  # Includes full path
  ELASTIC_IP = os.environ['ELASTIC_IP']
  ELASTIC_PORT = os.environ['ELASTIC_PORT']
  INDEX_NAME = os.environ['REPORT_ELASTIC_INDEX']
  DOC_TYPE = os.environ['REPORT_ELASTIC_DOC_TYPE']

  es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])

  # Get the list of report files to be scanned
  with open(input_filenames, 'r') as f:
    files = f.read().split('\n')
    # files = [f for f in files if 'Report_3697328.txt' in f]
    # files = files[0:5000] # limit number to ingest

  t0 = time.time()
  
  # Bulk load elastic
  print('Bulk chunk_size = {}'.format(args.num))
  res = helpers.bulk(es, load_reports(), chunk_size=args.num, max_chunk_bytes=500000000, max_retries=1, raise_on_error=False, raise_on_exception=False) # 500 MB
  log.info('Bulk insert result: %s, %s' % (res[0], res[1]))

  # Update Index
  es.indices.refresh(index=INDEX_NAME)

  # Print Summary
  res = es.search(index=INDEX_NAME, body={"query": {"match_all": {}}})
  log.info("Number of Search Hits: %d" % res['hits']['total'])
  elapsed_time = time.time() - t0
  ingest_rate = len(files) / elapsed_time
  log.info('{} files loaded to Elastic Search '.format(len(files)) + 'in {:.2f} seconds.'.format(elapsed_time))
  log.info('Ingest rate (files/s): {:.2f}'.format(ingest_rate))
  log.info('Finished.')

