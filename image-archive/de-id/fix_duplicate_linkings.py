#!/usr/bin/env python3
#
# File Description:
# Fixing duplicates means finding linkings with the same original value that have an older timestamp (they were added because ElasticSearch data doesn't become available immediately), then finding and updating the DICOM files where the duplicates were used, then removing the duplicates from the linking table. This is a syncronous operation (or can be split by orig keys into parallel jobs) to fix the problems (more than one linking given an original value, due to race condition) of the async coordination method that was used to create the linking table (avoid the problem because it's HARD, fix after is easier). Why not use a relational database with table locking? ie. lock table, insert linking, unlock, repeat to provide safe async linking? (https://stackoverflow.com/a/6621358/1631623)
#
# Pros of sql table locking: 
# - safe async
# - (con) During write actions, it must wait for all other sessions to be done with the table, and all other sessions must wait until the write is done. ie. 100+ million syncronous (x2 select then write). The benefit of using HPF is nullified if doing this! (not entirely as disk reads and other computation can still happen, but still this introduces a hard bottleneck where there was none before, everything else is scalable).
#
# Pros of elasticsearch avoid and fix async problem:
# - locking is HARD, has sublties
# - elastic is faster because of async inserting and faster for searching
# - don't have to learn to use and add a new database technology for this one task
# - sunk cost, I've already spent 3 hours on this approach :-(
#
# Decision: going to continue with async elastic search and fix because of reason above, see (con). Two parrallel passes (one to do linking and one to do fixing) is enough to solve the challenge of async computing, while maintaining scalability (doesn't have to be syncronous).
#
# Usage:
# source ../environments/local/env.sh
# python3.7 fix_duplicate_linkings.py && dicomdump tmp/*/*
#  | grep -i -e PatientName
#
# Note:
# Keep running this file until there are 0 duplicates
#
# Documentation:
# https://pyelasticsearch.readthedocs.io/en/latest/api/

import os
import sys
import uuid
import time
import pydicom
import logging
import datetime
import argparse

import elasticsearch
from random import randint
from elasticsearch import Elasticsearch
from elasticsearch import helpers

# from IPython import embed
# embed() # drop into an IPython session

## Change logging level for deid library (see ./logger/message.py for levels)
# from deid.logger import bot
# bot.level=5

logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
                    # level=logging.WARN)
                    # level=logging.DEBUG)
log = logging.getLogger('main')

ENVIRON = os.environ['ENVIRON']
ELASTIC_IP = os.environ['ELASTIC_IP']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
FALLBACK_ELASTIC_IP = os.environ['FALLBACK_ELASTIC_IP']
FALLBACK_ELASTIC_PORT = os.environ['FALLBACK_ELASTIC_PORT']
INDEX_NAME = os.environ['ELASTIC_INDEX']
DOC_TYPE = os.environ['ELASTIC_DOC_TYPE']
LINKING_INDEX_NAME = os.environ['LINKING_ELASTIC_INDEX']
LINKING_DOC_TYPE = os.environ['LINKING_ELASTIC_DOC_TYPE']
FILESERVER_TOKEN = os.getenv('FILESERVER_TOKEN','')
FILESERVER_DICOM_PATH = os.environ['FILESERVER_DICOM_PATH']
FILESERVER_THUMBNAIL_PATH = os.environ['FILESERVER_THUMBNAIL_PATH']


if __name__ == '__main__':
  # Set up command line arguments
  parser = argparse.ArgumentParser(description='Looks up documents in ElasticSearch, finds the DICOM files, processes them, and saves a copy.')  

  t0 = time.time()
  count = 0

  # Get linkings from ElasticSearch
  es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])
  query = {
    "size": 0,
    "aggs" : {
      "count_orig" : {
        "terms" : { "field" : "orig.keyword" }
      }
    }
  }
  results = es.search(body=query, index=LINKING_INDEX_NAME, doc_type=LINKING_DOC_TYPE)

  # Find the values which have a count greater than 1
  duplicates = [agg['key'] for agg in results['aggregations']['count_orig']['buckets'] if agg['doc_count']>1]

  # Loop over duplicates found in linking table, fixing duplicates
  for dup in duplicates:
    query = { "query": 
      {"term": { 
        "orig.keyword": dup}
      },
      "size": 5000, # run this file more than once if there are really more than 5000 duplicates (really shouldn't be)
      "sort" : [
         {"date" : {"order" : "asc"}}
      ]
    }
    res = es.search(body=query, index=LINKING_INDEX_NAME)
    res = res['hits']['hits']
    uniq_dict = res.pop(0) # the first is the oldest, we want to use that as the fix/replacement value
    dup_dicts = res # the rest need to be fixed
    true_value = uniq_dict['_source']['new'] # this is the true linking value that we want to fix/replace duplicates with

    # For this duplicate, update all of the duplicates to use value given by the unique (first/oldest) linking
    for dup_dict in dup_dicts:
      filename = dup_dict['_source']['new_path']
      field = dup_dict['_source']['field']
      log.info('Setting field "%s" to "%s" in file: %s' % (field, true_value, filename))
      count = count + 1

      # Modify DICOM file
      ds = pydicom.dcmread(filename)
      setattr(ds, field, true_value) # fix the linking
      ds.save_as(filename)

      # Delete duplicate in ES linking table
      es.delete(id=dup_dict['_id'], index=LINKING_INDEX_NAME, doc_type=LINKING_DOC_TYPE)

  # # Print Summary
  elapsed_time = time.time() - t0
  ingest_rate = count / elapsed_time
  log.info('{} updates processed '.format(count) + 'in {:.2f} seconds.'.format(elapsed_time))
  log.info('Processing rate (updates/s): {:.2f}'.format(ingest_rate))
  log.info('Finished.')
