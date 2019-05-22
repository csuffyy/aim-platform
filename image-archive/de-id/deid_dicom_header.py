#!/usr/bin/env python3
#
# File Description:
# Looks up documents in ElasticSearch, finds the DICOM files, processes them, and saves a copy.
#
# Usage:
# source ../environments/local/env.sh
# python3.7 deid_dicom_header.py -input_range 1-10 -output_folder ./tmp/
#  | grep -i -e PatientName
#
# Documentation:
# https://github.com/pydicom/deid/tree/master/deid/dicom
# https://github.com/pydicom/deid/blob/master/deid/dicom/header.py#L242
# https://pyelasticsearch.readthedocs.io/en/latest/api/

import os
import sys
import time
import uuid
import logging
import datetime
import argparse

import elasticsearch
from random import randint
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from deid.config import DeidRecipe
from deid.dicom import get_files, replace_identifiers, get_identifiers

from IPython import embed
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

save_to_elastic = True
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


def lookup_linking(orig):
  # Look to find existing linking in ElasticSearch
  query = { "query": 
    {"term": { 
      "orig.keyword": orig}
    },
    "sort" : [
       {"date" : {"order" : "asc"}}
    ]
  }
  try:
    res = es.search(body=query, index=LINKING_INDEX_NAME)
    res = res['hits']['hits']
  except elasticsearch.exceptions.RequestError as e:
    # elasticsearch.exceptions.RequestError: RequestError(400, 'search_phase_execution_exception', 'No mapping found for [date] in order to sort on')
    if 'No mapping found' in e.info['error']['root_cause'][0]['reason']:
      res = [] # mapping just doesn't exist yet
    else:
      raise e
  return res

def generate_uid(dicom_dict, function_name, field_name):
  orig = dicom_dict[field_name] if field_name in dicom_dict else ''
  uid = str(uuid.uuid4()) # otherwise generate new id

  # Look to find existing linking in ElasticSearch
  if save_to_elastic:
    res = lookup_linking(orig)

    if len(res):
      uid = res[0]['_source']['new'] # use id found in elastic
    else:
      query = {'orig': orig, 'new': uid, 'field': field_name, 'date': datetime.datetime.now(), 'orig_path': dicom_dict['orig_path'], 'new_path': dicom_dict['new_path']}
      if '_id' in dicom_dict:
        query['id'] = dicom_dict['_id'] # Use same elasticsearch document ID from input index in the new index
      res = es.index(body=query, index=LINKING_INDEX_NAME, doc_type=LINKING_DOC_TYPE)

    log.info('Linking %s:%s-->%s' % (field_name, orig, uid))

  return uid
  
# def generate_date_uid(dicom_dict, function_name, field_name):
#   orig = dicom_dict[field_name] if field_name in dicom_dict else ''
#   es_id = dicom_dict['_id'] # ID for elasticsearch document

#   # Look to find existing linking in ElasticSearch
#   res = lookup_linking(orig)

#   if len(res):
#     uid = res[0]['_source']['new'] # use id found in elastic
#   else:
#     uid=datetime.date(randint(1000,9999), randint(1,12),randint(1,28))
#     res = es.index(body={'orig': orig, 'new_date': uid, 'id':es_id, 'field': field_name, 'date': datetime.datetime.now(), 'dicom_filepath': dicom_dict['dicom_filepath']}, index=LINKING_INDEX_NAME, doc_type=LINKING_DOC_TYPE)

#   log.info('[%s] Linking %s:%s-->%s' % (es_id, field_name, orig, uid))

#   return uid

if __name__ == '__main__':
  # Set up command line arguments
  parser = argparse.ArgumentParser(description='Looks up documents in ElasticSearch, finds the DICOM files, processes them, and saves a copy.')
  parser.add_argument('--input_range', help='Positional document numbers in ElasticSearch (ex. 1-10). These documents will be processed.')
  parser.add_argument('--input_files', help='List of DICOM files which will be processed.')
  parser.add_argument('--no_elastic', action='store_true', help='Skip saving metadata to ElasticSearch.')
  parser.add_argument('--deid_recipe', default='deid.dicom', help='De-id rules.')
  parser.add_argument('--output_folder', help='Save processed DICOM files to this path.')
  args = parser.parse_args()
  output_folder = args.output_folder
  save_to_elastic = not args.no_elastic
  input_range = args.input_range
  input_files = args.input_files
  deid_recipe = args.deid_recipe
  recipe = DeidRecipe(deid_recipe) # de-id rules

  if input_files:
    # # Get List of Dicoms
    fp = open(input_files) # Open file on read mode
    dicom_paths = fp.read().split("\n") # Create a list containing all lines
    fp.close() # Close file
    dicom_paths = list(filter(None, dicom_paths)) # remove empty lines
    doc_ids = None

  if save_to_elastic:
    es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])

  if input_range:
    # Get documents from ElasticSearch
    input_start, input_end = [int(i) for i in input_range.split('-')]
  
    query = {
      "_source": ["_id", "dicom_filepath"],
      "from": input_start,
      "size": input_end
    }
    results = es.search(body=query, index=INDEX_NAME, doc_type=DOC_TYPE)
    log.info("Number of Search Hits: %d" % len(results['hits']['hits']))
    results = results['hits']['hits']
    dicom_paths = [res['_source']['dicom_filepath'] for res in results]

    doc_ids = [res['_id'] for res in results]

  # Prepare documents for de-identification
  dicom_dicts = get_identifiers(dicom_paths)
  for idx, path in enumerate(dicom_dicts):
    # Remember, the action is: 
    # REPLACE StudyInstanceUID func:generate_uid
    # so the key needs to be generate_uid
    filename = os.path.basename(path)
    folder_prefix = os.path.basename(os.path.dirname(path))
    folderpath = os.path.join(output_folder, folder_prefix)
    filepath = os.path.join(folderpath, filename)
    dicom_dicts[path]['new_path'] = filepath
    dicom_dicts[path]['orig_path'] = path
    dicom_dicts[path]['generate_uid'] = generate_uid
    # dicom_dicts[path]['generate_date_uid'] = generate_date_uid
    if save_to_elastic and input_range:
      dicom_dicts[path]['_id'] = str(doc_ids[idx]) # Store elasticsearch document id

  t0 = time.time()

  # Loop over dicoms and De-Identify
  for dicom_path, dicom_dict in dicom_dicts.items():
    log.debug('Processing DICOM path: %s' % path)
    str_linking = []
    date_linking = []
    item = {dicom_path: dicom_dict}

    # De-Identify Metadata
    cleaned_files = replace_identifiers(dicom_files=dicom_path,
                                        deid=recipe,
                                        ids=item,
                                        save=False,
                                        remove_private=False)
                                        # overwrite=True,
                                        # output_folder=output_folder)

    # # Insert linkings into master linking list in ElasticSearch
    # docs = (linking for linking in str_linking)
    # res = helpers.bulk(es, docs, index=LINKING_INDEX_NAME, doc_type=LINKING_DOC_TYPE, chunk_size=1000, max_chunk_bytes=500000000, max_retries=1, raise_on_error=True, raise_on_exception=True) # 500 MB
    # log.info("Inserted %s linkings into ElasticSearch" % res[0])

    # import time
    # time.sleep(.5)
    # es.indices.refresh(index=LINKING_INDEX_NAME)

    for ds in cleaned_files:
      # De-identify Pixels
      embed()

      # Save DICOMs to disk
      filename = os.path.basename(dicom_path)
      folder_prefix = os.path.basename(os.path.dirname(dicom_path))
      folderpath = os.path.join(output_folder, folder_prefix)
      filepath = os.path.join(folderpath, filename)
      if not os.path.exists(folderpath):
          os.makedirs(folderpath)
      ds.save_as(filepath)

  # from IPython import embed
  # embed() # drop into an IPython session


  # Print Summary
  elapsed_time = time.time() - t0
  ingest_rate = len(dicom_dicts) / elapsed_time
  log.info('{} documents processed '.format(len(dicom_dicts)) + 'in {:.2f} seconds.'.format(elapsed_time))
  log.info('Processing rate (documents/s): {:.2f}'.format(ingest_rate))
  log.info('Finished.')
