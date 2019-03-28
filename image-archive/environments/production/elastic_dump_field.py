from elasticsearch import Elasticsearch
import json


logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
                    # level=logging.DEBUG)
log = logging.getLogger('main')

ELASTIC_IP = os.environ['ELASTIC_IP']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
INDEX_NAME = os.environ['ELASTIC_INDEX']
DOC_TYPE = os.environ['ELASTIC_DOC_TYPE']

# Process hits here
def process_hits(hits):
    for item in hits:
        print(json.dumps(item, indent=2))

if __name__ == '__main__':
  # Set up command line arguments
  parser = argparse.ArgumentParser(description='Load dicoms to Elastic.')
  parser.add_argument('field', help='Field.')
  args = parser.parse_args()
  field = args.field

  # Define config
  scroll_size = 5000
  search_body = {
    "_source":[field]
  }

  # Init Elasticsearch instance
  es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])

  # Check index exists
  if not es.indices.exists(index=ELASTIC_INDEX):
    print("Index " + ELASTIC_INDEX + " not exists")
    exit()

  # Init scroll by search
  data = es.search(
    index=ELASTIC_INDEX,
    doc_type=ELASTIC_DOC_TYPE,
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
  dl_rate = len(hit_count) / elapsed_time
  log.info('{} documents loaded to Elastic Search '.format(len(hit_count)) + 'in {:.2f} seconds.'.format(elapsed_time))
  log.info('Download rate (documents/s): {:.2f}'.format(dl_rate))
  log.info('Finished.')
