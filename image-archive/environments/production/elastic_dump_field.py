# Usage:
# python3 image-archive/environments/production/elastic_dump_field.py report Report > ~/380375_Reports_for_Chris.json
# ./scp -i ~/.ssh/id_rsa_CCM ubuntu@172.20.4.83:~/380375_Reports_for_Chris.json ./

import os
import sys
import json
import time
import argparse

from elasticsearch import Elasticsearch

ELASTIC_IP = os.environ['ELASTIC_IP']
ELASTIC_PORT = os.environ['ELASTIC_PORT']


# Process hits here
def process_hits(hits):
  print('.', end='', file=sys.stderr, flush=True)
  for item in hits:
    record = {
      'id': item['_id'],
      field: item['_source'][field]
    }
    print(json.dumps(record, indent=2) + ',') # PRINT ONE FIELD
    # print(json.dumps(item, indent=2) + ',') # PRINT ALL FIELDS


if __name__ == '__main__':
  # Set up command line arguments
  parser = argparse.ArgumentParser(description='Load dicoms to Elastic.')
  parser.add_argument('index_name', help='Elasticsearch index and field name.')
  parser.add_argument('field', help='Elasticsearch index field.')
  args = parser.parse_args()
  field = args.field
  index_name = args.index_name

  # Define config
  scroll_size = 5000
  search_body = {
    "_source":[field]
  }

  # Init Elasticsearch instance
  es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])

  # Check index exists
  if not es.indices.exists(index=index_name):
    print("Index " + index_name + " not exists")
    exit()

  # Init scroll by search
  data = es.search(
    index=index_name,
    doc_type=index_name,
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
  print('\n{} documents loaded to Elastic Search '.format(hit_count) + 'in {:.2f} seconds.'.format(elapsed_time), file=sys.stderr)
  print('Download rate (documents/s): {:.2f}'.format(dl_rate), file=sys.stderr)
