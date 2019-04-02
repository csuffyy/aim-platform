
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

files = [
         '/home/dan/testcases/126309921.dcm-0TO0-771100.dcm',
         '/home/dan/testcases/91621477.dcm-0TO0-771100.dcm',
         '/home/dan/testcases/113254338.dcm-0TO0-771100.dcm',
         '/home/dan/testcases/113254338.dcm-0TO0-771100.dcm',
         '/home/dan/testcases/126559797.dcm-0TO0-771100.dcm',
         '/home/dan/testcases/00061_1.2.840.113663.1500.1.193471476.3.61.20060405.91134.562-rt-trans.dcm',
         '/home/dan/testcases/118389427.dcm-0TO0-771100.dcm',
         '/home/dan/testcases/119783495.dcm-0TO0-771100.dcm',
         '/home/dan/testcases/XA-MONO2-8-12x-catheter.dcm',
         '/home/dan/testcases/86178171.dcm',
         '/home/dan/testcases/86514981.dcm',
         '/home/dan/testcases/88820209.dcm',
         '/home/dan/testcases/90408284.dcm',
         '/home/dan/testcases/92939088.dcm',
         '/home/dan/testcases/ExplVR_BigEnd.dcm',
         '/home/dan/testcases/93721396.dcm'
         ]


output_path = '/home/dan/testcases'

logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
                    # level=logging.DEBUG)
log = logging.getLogger('main')


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
  smallest_dimension = np.sort(img.shape)[0]
  if len(img.shape) == 3 and smallest_dimension != 3: # 3 here means rgb, likely a z-stack
    img = img[int(img.shape[0]/2),:,:]
  # Handle rgbd Z stacks
  if len(img.shape) == 4 and smallest_dimension != 3: # 3 here means rgb, likely a z-stack
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
  max_height = 333.0
  max_width = 250.0
  ratio = np.min([max_width / img.shape[0], max_height / img.shape[1]])
  resize_width = int(img.shape[0]*ratio)
  resize_height = int(img.shape[1]*ratio)
  im_resized = cv2.resize(img, dsize=(resize_height, resize_width), interpolation=cv2.INTER_CUBIC)
  p2, p98 = np.percentile(im_resized, (0.5, 99.5))
  im_resized = np.interp(im_resized, (p2, p98), (0, 255)) # rescale between min and max
  filename = os.path.basename(filepath)
  thumbnail_filename = '%s.png' % filename
  thumbnail_filepath = os.path.join(output_path, thumbnail_filename)
  cv2.imwrite(thumbnail_filepath, im_resized);
  # plt.imshow(im_resized, cmap='gray')
  # plt.show()
  log.info('Saved thumbnail: %s' % thumbnail_filepath)
  return thumbnail_filepath


for filepath in files:
  # Load Image
  dicom = pydicom.dcmread(filepath, force=True)
  dicom_metadata = {}
  [dicom_metadata.__setitem__(key,str(dicom.get(key))) for key in dicom.dir() if key not in ['PixelData']]
  # import sys
  # o=[sys.getsizeof(v) for k, v in dicom_metadata.items()]
  # embed()

  
  # dicom_metadata
  # embed()
  thumbnail_filepath = save_thumbnail_of_dicom(dicom, filepath)
