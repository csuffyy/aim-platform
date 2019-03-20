
#!/bin/python
#
# Usage:
# source ../environments/local/env.sh
# python3 load_elastic.py ../images/sample-dicom/image_list.txt ../reactive-search/static/thumbnails/

# module load python/3.7.1_GDCM

import os 
import cv2
import glob
import random
import pydicom
import logging
import traceback
import numpy as np
import argparse
import pickle
import elasticsearch.exceptions
import time

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from IPython import embed

import matplotlib
from matplotlib import pyplot as plt
# matplotlib.use('TkAgg')


def save_thumbnail_of_dicom(dicom, filepath):
  try:
    img = dicom.pixel_array
  except Exception as e:
    print(traceback.format_exc())
    log.warning('Skipping this image because error occured when reading pixel_array')
    return

  # Image shape
  if img.shape == 0:
    log.warning('Image size is 0: %s' % filepath)
    return
  # Handle greyscale Z stacks
  if len(img.shape) == 3 and img.shape[0] > 3:
    img = img[int(img.shape[0]/2),:,:]
  # Handle rgbd Z stacks
  if len(img.shape) == 4 and img.shape[0] > 3:
    img = img[int(img.shape[0]/2),:,:,:]
  if len(img.shape) not in [2,3]:
    log.warning('Image shape is not supported: %s' % filepath)
    return
      
  # Colorspace
  if 'PhotometricInterpretation' in dicom and 'YBR' in dicom.PhotometricInterpretation:
    # Convert from YBR to RGB
    image = Image.fromarray(img,'YCbCr')
    image = image.convert('RGB')
    img = np.array(image)
    # plt.imshow(img, cmap='gray')
    # plt.show()
    # More image modes: https://pillow.readthedocs.io/en/3.1.x/handbook/concepts.html#concept-modes
  if 'PhotometricInterpretation' in dicom and 'RGB' in dicom.PhotometricInterpretation:
    img = img[...,::-1]

  # Calculate thumnail size while retaining preportions
  max_height = 333
  max_width = 250
  if img.shape[1] / max_width > img.shape[0] / max_height:
      # It must be fixed by width
      resize_width = max_width
      resize_height = round(img.shape[1] / (img.shape[1] / max_width))
  else:
      # Fixed by max_height
      resize_width = round(img.shape[0] / (img.shape[0] / max_height))
      resize_height = max_height

  im_resized = cv2.resize(img, dsize=(resize_width, resize_height), interpolation=cv2.INTER_CUBIC)
  im_resized = np.interp(im_resized, (im_resized.min(), im_resized.max()), (0, 255))
  filename = os.path.basename(filepath)
  thumbnail_filename = '%s.png' % filename
  thumbnail_filepath = os.path.join(output_path, thumbnail_filename)
  cv2.imwrite(thumbnail_filepath, im_resized);
  # plt.imshow(im_resized, cmap='gray')
  # plt.show()
  log.info('Saved thumbnail: %s' % thumbnail_filepath)
  return thumbnail_filepath


def load_images():
  for filepath in files:
    # filepath = mll[file]

    # Load Image
    dicom = pydicom.dcmread(filepath, force=True)
    dicom_metadata = {}
    [dicom_metadata.__setitem__(key,dicom.get(key)) for key in dicom.dir() if key not in ['PixelData']]

    log.info('\n\n')
    log.info('Processing: %s' % filepath)
    for key, value in dicom_metadata.items():
      if hasattr(dicom_metadata[key], '_list'):
        # Fix for error: TypeError("Unable to serialize ['ORIGINAL', 'SECONDARY'] (type: <class 'pydicom.multival.MultiValue'>)")
        dicom_metadata[key] = dicom_metadata[key]._list
      if hasattr(dicom_metadata[key], 'original_string'):
        # Fix for error: TypeError("Unable to serialize '' (type: <class 'pydicom.valuerep.PersonName3'>)")
        dicom_metadata[key] = dicom_metadata[key].original_string
      if isinstance(dicom_metadata[key], bytes):
        # Fix for error: TypeError("Unable to serialize b'FOONAME^BARNAM' (type: <class 'bytes'>)")
        try:
          dicom_metadata[key] = dicom_metadata[key].decode("utf-8")
        except UnicodeDecodeError as e:
          pass
      if isinstance(dicom_metadata[key], list):
        if len(dicom_metadata[key])>0 and type(dicom_metadata[key][0]) is pydicom.dataset.Dataset:
          # Fix for error: TypeError("Unable to serialize 'ProcedureCodeSequence' (type: <class 'pydicom.dataset.Dataset'>)")")
          dicom_metadata[key] = dicom_metadata[key].__str__()

      log.debug('%s: %s' % (key, value))

    if 'TransferSyntaxUID' not in dicom.file_meta:
      # Guess a transfer syntax if none is available
      dicom.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian  # 1.2.840.10008.1.2
      dicom.add_new(0x19100e, 'FD', [0,1,0]) # I have no idea what this last vector should actually be
      dicom[0x19100e].value = 'Assumed TransferSyntaxUID'
      log.warning('Assumed TransferSyntaxUID')
    # PatientBirthDatePretty
    try:
      if 'PatientBirthDate' in dicom_metadata:
        PatientBirthDate = datetime.strptime(dicom_metadata['PatientBirthDate'], '%Y%m%d')
        dicom_metadata['PatientBirthDatePretty'] = datetime.strftime(PatientBirthDate,'%Y-%m-%d')
    except:
      log.warning('Didn\'t understand value: %s = \'%s\'' % ('PatientBirthDate', dicom_metadata['PatientBirthDate']))
    # AcquisitionDatePretty
    try:
      if 'AcquisitionDate' in dicom_metadata:
        AcquisitionDate = datetime.strptime(dicom_metadata['AcquisitionDate'], '%Y%m%d')
        dicom_metadata['AcquisitionDatePretty'] = datetime.strftime(AcquisitionDate,'%Y-%m-%d')
    except:
      log.warning('Didn\'t understand value: %s = \'%s\'' % ('AcquisitionDate', dicom_metadata['AcquisitionDate']))
    # PatientAgeInt (Method 1: diff between birth and acquisition dates)

    # Remove bytes datatype from metadata because it can't be serialized for sending to elasticsearch
    filtered = {k: v for k, v in dicom_metadata.items() if type(v) is not bytes}
    dicom_metadata.clear()
    dicom_metadata.update(filtered)

    # Convert any values that can be displayed as a string (things that need to be numbers should follow this)
    for k, v in dicom_metadata.items():
      # convert to string if not already a string and has str method
      if not isinstance(v,str) and '__str__' in dir(v):
        dicom_metadata[k] = dicom_metadata[key].__str__()

    try:
      if 'PatientBirthDate' in dicom_metadata and 'AcquisitionDate' in dicom_metadata:
        PatientBirthDate = datetime.strptime(dicom_metadata['PatientBirthDate'], '%Y%m%d')
        AcquisitionDate = datetime.strptime(dicom_metadata['AcquisitionDate'], '%Y%m%d')
      age = AcquisitionDate - PatientBirthDate
      age = int(age.days / 365) # age in years
      dicom_metadata['PatientAgeInt'] = age
    except:
      log.warning('Falling back for PatientAge')
    # PatientAgeInt (Method 2: str to int)
    try:
      if 'PatientAge' in dicom_metadata:
        age = dicom_metadata['PatientAge'] # usually looks like '06Y'
        if 'Y' in age:
          age = age.split('Y')
          age = int(age[0])
          dicom_metadata['PatientAgeInt'] = age
    except:
      log.warning('Didn\'t understand value: %s = \'%s\'' % ('PatientAge', dicom_metadata['PatientAge']))
    # DEMO ONLY!!!! Add random age
    # if 'PatientAgeInt' not in dicom_metadata:
    #   dicom_metadata['PatientAgeInt'] = random.randint(1,20)


    thumbnail_filepath = save_thumbnail_of_dicom(dicom, filepath)
    if not thumbnail_filepath:
      log.warning('Skipping this dicom. Could not generate thumbnail.')
      continue

    # Save Path of DICOM
    # Example: 172.20.4.85:8000/static/dicom/OT-MONO2-8-hip.dcm-0TO0-771100.dcm
    dicom_filename = os.path.basename(filepath)
    dicom_token = FILESERVER_TOKEN
    if FILESERVER_TOKEN != '': # when using a token, add .dcm to the end of the URL so that DWV will accept the file
      dicom_token = FILESERVER_TOKEN + '.dcm'
    dicom_metadata['dicom_filename'] = dicom_filename
    dicom_path = filepath.replace(FILESERVER_DICOM_PATH,'')
    dicom_metadata['dicom_filepath'] = '{ip}:{port}/{path}{token}'.format(ip=FILESERVER_IP, port=FILESERVER_PORT, path=dicom_path, token=dicom_token)

    # Save Path of Thumbnail
    # Example: http://172.20.4.85:8000/static/thumbnails/testplot.png-0TO0-771100
    thumbnail_filename = os.path.basename(thumbnail_filepath)
    dicom_metadata['thumbnail_filename'] = thumbnail_filename
    dicom_metadata['thumbnail_filepath'] = 'http://{ip}:{port}/{path}/{filename}{token}'.format(ip=FILESERVER_IP, port=FILESERVER_PORT, path=FILESERVER_THUMBNAIL_PATH, filename=thumbnail_filename, token=FILESERVER_TOKEN)

    dicom_metadata['original_title'] = 'Dicom'
    dicom_metadata['_index'] = INDEX_NAME
    dicom_metadata['_type'] = DOC_TYPE
    dicom_metadata['searchallblank'] = '' # needed to search across everything (via searching for empty string)
    yield dicom_metadata


if __name__ == '__main__':
  # Set up command line arguments
  parser = argparse.ArgumentParser(description='Load dicoms to Elastic.')
  parser.add_argument('input_filenames', help='File containing dicom file names.')
  parser.add_argument('output_path', help='File containing dicom file names.')
  parser.add_argument('-n', '--num', type=int, default=500,
                      help='Bulk chunksize.')
  args = parser.parse_args()
  input_filenames = args.input_filenames  # Includes full path
  output_path = args.output_path


  ELASTIC_IP = os.environ['ELASTIC_IP']
  ELASTIC_PORT = os.environ['ELASTIC_PORT']
  FALLBACK_ELASTIC_IP = os.environ['FALLBACK_ELASTIC_IP']
  FALLBACK_ELASTIC_PORT = os.environ['FALLBACK_ELASTIC_PORT']
  INDEX_NAME = os.environ['ELASTIC_INDEX']
  DOC_TYPE = os.environ['ELASTIC_DOC_TYPE']
  FILESERVER_IP = os.environ['FILESERVER_IP']
  FILESERVER_PORT = os.environ['FILESERVER_PORT']
  FILESERVER_TOKEN = os.getenv('FILESERVER_TOKEN','')
  FILESERVER_DICOM_PATH = os.environ['FILESERVER_DICOM_PATH']
  FILESERVER_THUMBNAIL_PATH = os.environ['FILESERVER_THUMBNAIL_PATH']

  # output_path = '/hpf/largeprojects/diagimage_common/shared/thumbnails'
  # output_path = '/home/chuynh/aim-platform/image-archive/de-id/jobs/thumbnails'
  # Create out directory if it does not exist.
  if not os.path.isdir(output_path):
    os.makedirs(output_path)

  logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                      datefmt='%H:%M:%S',
                      level=logging.INFO)
                      # level=logging.DEBUG)
  log = logging.getLogger('main')

  es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])

  # Test ElasticSearch connection and fallback if it fails
  '''
  try:
    es.indices.refresh(index=INDEX_NAME)
  # except elasticsearch.exceptions.ConnectionError as e:
  except Exception as e:
    log.warning('Trying Fallback ElasticSearch IP')
    es = Elasticsearch([{'host': FALLBACK_ELASTIC_IP, 'port': FALLBACK_ELASTIC_PORT}])
    es.indices.refresh(index=INDEX_NAME)
  '''

  # Just going to add code here for now...
  # Get the list of dicom files to be scanned
  with open(input_filenames, 'r') as f:
    files = f.read().split('\n')
    files = files[0:5000]
    del files[-1]  # Remove blank item

  # # Get master linking log (do we still need this? maybe not...)
  # fn = input_filenames.split('.')[0]
  # jobdir = os.path.dirname(fn)
  # mll_fn = os.path.join(jobdir, 'mll')
  # with open(mll_fn, 'rb') as h:
  #   mll = pickle.load(h)

  t0 = time.time()
  
  # Bulk load elastic
  print('Bulk chunk_size = {}'.format(args.num))
  res = helpers.bulk(es, load_images(), chunk_size=args.num, max_chunk_bytes=500000000, max_retries=1) # 500 MB
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

  # Write parameters
  CPU = os.getenv('CPU',None)
  RAM = os.getenv('RAM',None)
  if CPU and RAM:
    stats_filename = '/home/chuynh/kiddata/stats.csv'
    with open(stats_filename, 'a') as file_handle:
      file_handle.write(RAM + ',')
      file_handle.write(CPU + ',')
      file_handle.write(str(args.num) + ',')
      file_handle.write(str(ingest_rate) + '\n')
