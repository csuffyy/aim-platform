#!/usr/bin/env python3
#
# File Description:
# Looks up documents in ElasticSearch, finds the DICOM files, processes them, and saves a copy.
#
# Usage:
# source ../environments/local/env.sh
# python3.7 deid_dicoms.py --input_range 1-10 --output_folder ./tmp/
# OR
# python3.7 deid_dicoms.py --input_filelist ~/Favourite_Images/file_list.txt --output_folder ./tmp/
# OR
# python3.5 deid_dicoms.py --input_file /home/dan/823-whole-body-MR-with-PHI.dcm --output_folder ./tmp/ --fast_crop
# OR
# kill %; pkill -9 eog; pkill display; python3.5 deid_dicoms.py --output_folder ./tmp/ --gif --disp --input_folder /home/dan/Favourite_Images/Requisition/
# OR
# kill %; pkill -9 eog; pkill display; python3.5 deid_dicoms.py --output_folder ~/aim-platform/image-archive/reactive-search/static/deid/ --gif --disp --input_file ../images/sample/CT-MONO2-16-ort.dcm --wait --fast_crop --input_base_path /home/dan/aim-platform/image-archive/images/ --input_report_base_path /home/dan/aim-platform/image-archive/reports/
#
# Note:
# If you get error "OSError: cannot identify image file", try using python3 instead of python3.7
#
# Documentation:
# https://github.com/pydicom/deid/tree/master/deid/dicom
# https://github.com/pydicom/deid/blob/master/deid/dicom/header.py#L242
# https://pyelasticsearch.readthedocs.io/en/latest/api/

import os
import re
import cv2
import sys
import glob
import time
import math
import uuid
import pickle
import random
import pydicom
import logging
import datetime
import argparse
import traceback
import datefinder
import matplotlib
import pytesseract
import collections
import numpy as np
import pandas as pd
import elasticsearch

from IPython import embed
# embed() # drop into an IPython session
from skimage import feature
from random import randint
from itertools import chain
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from elasticsearch import helpers
from deid.config import DeidRecipe
from matplotlib import pyplot as plt
from elasticsearch import Elasticsearch
from dateparser.search import search_dates
from dateutil.relativedelta import relativedelta
from skimage.morphology import white_tophat, opening, disk
from deid.dicom import get_files, replace_identifiers, get_identifiers
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True # fixes OSError: broken data stream when reading image file 

from utils import dicom_to_dict

## Change logging level for deid library (see ./logger/message.py for levels)
# from deid.logger import bot
# bot.level=5

# Change logging level for pyelasticsearch library
logging.getLogger('elasticsearch.trace').setLevel(logging.WARN)
logging.getLogger('elasticsearch').setLevel(logging.WARN)

logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    # level=logging.DEBUG)
                    level=logging.INFO)
                    # level=logging.WARN)
log = logging.getLogger('main')

# Settings
ELASTIC_IP = os.environ['ELASTIC_IP']
ELASTIC_PORT = os.environ['ELASTIC_PORT']
INDEX_NAME = os.environ['ELASTIC_INDEX']
DOC_TYPE = os.environ['ELASTIC_DOC_TYPE']
LINKING_INDEX_NAME = os.environ['LINKING_ELASTIC_INDEX']
LINKING_DOC_TYPE = os.environ['LINKING_ELASTIC_DOC_TYPE']
COUNT_INDEX_NAME = os.environ.get('COUNT_ELASTIC_INDEX','count')
COUNT_DOC_TYPE = os.environ.get('COUNT_ELASTIC_DOC_TYPE','count')
REPORT_INDEX_NAME = os.environ.get('REPORT_ELASTIC_INDEX','report')
REPORT_DOC_TYPE = os.environ.get('REPORT_ELASTIC_DOC_TYPE','report')
DEID_REPORT_INDEX_NAME = os.environ.get('DEID_REPORT_ELASTIC_INDEX','deid_report')
DEID_REPORT_DOC_TYPE = os.environ.get('DEID_REPORT_ELASTIC_DOC_TYPE','deid_report')
ENVIRON = os.environ['ENVIRON']
FILESERVER_IP = os.environ['FILESERVER_IP']
FILESERVER_PORT = os.environ['FILESERVER_PORT']
FILESERVER_TOKEN = os.environ.get('FILESERVER_TOKEN','')
FILESERVER_DICOM_PATH = os.environ['FILESERVER_DICOM_PATH']
FILESERVER_THUMBNAIL_PATH = os.environ['FILESERVER_THUMBNAIL_PATH']
MATCH_CONF_THRESHOLD = 50
TOO_MUCH_TEXT_THRESHOLD = 0
MAX_NUM_PIXELS = 36000000 # 36 million pixels calculated as 2000x2000 plus RESIZE_FACTOR=3, so 6000x6000. Anymore takes too long)
RESIZE_FACTOR = 3 # how much to blow up image to make OCR work better


def add_derived_fields(dicom):
  log.info('Adding derived fields.')

  # Calculate PatientAge
  PatientBirthDate = dicom.get('PatientBirthDate')
  AcquisitionDate = dicom.get('AcquisitionDate')
  PatientAge = dicom.get('PatientAge')

  # PatientAgeInt (Method 1: str to int)
  try:
    if PatientAge is not None:
      age = PatientAge # usually looks like '06Y'
      if 'Y' in PatientAge:
        age = PatientAge.split('Y')
        age = int(age[0])
      dicom.PatientAge = str(age)
  except:
    log.warning('Falling back for PatientAge')
  # PatientAgeInt (Method 2: diff between birth and acquisition dates)
  # Note: Method 2 is higher precision (not just year) and will override method one
  try:
    if PatientBirthDate is not None and AcquisitionDate is not None:
      PatientBirthDate = datetime.datetime.strptime(PatientBirthDate, '%Y%m%d')
      AcquisitionDate = datetime.datetime.strptime(AcquisitionDate, '%Y%m%d')
    age = AcquisitionDate - PatientBirthDate
    age = round(age.days / 365,2) # age in years with two decimal place precision
    dicom.PatientAge = str(age)
    log.debug('Calculated PatientAge to be: %s' % age)
  except Exception as e:
    log.warning('Couldn\'t calculate PatientAgeInt')

  # # Add fake data for local testing only! TODO: Commented out because this is dangerous and has caused me confusion
  if ENVIRON=='local':
    if 'PatientAge' not in dicom:
      log.warning('Adding fake PatientAge')
      dicom.PatientAge = str(random.randint(1,18))
    if 'PatientSex' not in dicom:
      log.warning('Adding fake PatientSex')
      dicom.PatientSex = 'Male' if random.randint(0,1) else 'Female'

def convert_colorspace(img, dicom):
  if 'PhotometricInterpretation' in dicom and isinstance(dicom.PhotometricInterpretation, str):
    if 'YBR' in dicom.PhotometricInterpretation:
      # Convert from YBR to RGB
      image = Image.fromarray(img,'YCbCr')
      image = image.convert('RGB')
      img = np.array(image)
      # plt.imshow(img, cmap='gray')
      # plt.show()
      # More image modes: https://pillow.readthedocs.io/en/3.1.x/handbook/concepts.html#concept-modes
    if 'RGB' in dicom.PhotometricInterpretation:
      img = img[...,::-1]
  return img

def save_thumbnail_of_dicom(dicom):
  try:
    img = dicom.pixel_array
  except Exception as e:
    print(traceback.format_exc())
    log.warning('Skipping this image because error occured when reading pixel_array')
    log.warning('Problem image was: %s\n' % filepath)
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
  img = convert_colorspace(img, dicom)

  # Calculate thumnail size while retaining preportions
  max_height = 333.0
  max_width = 250.0
  ratio = np.min([max_width / img.shape[0], max_height / img.shape[1]])
  resize_width = int(img.shape[0]*ratio)
  resize_height = int(img.shape[1]*ratio)
  im_resized = cv2.resize(img, dsize=(resize_height, resize_width), interpolation=cv2.INTER_CUBIC)
  p2, p98 = np.percentile(im_resized, (0.5, 99.5)) # adjust brightness to improve thumbnail viewing
  im_resized = np.interp(im_resized, (p2, p98), (0, 255)) # rescale between min and max
  cv2.imwrite(output_thumbnail_filepath, im_resized);
  # # plt.imshow(im_resized, cmap='gray')
  # # plt.show()
  log.info('Saved thumbnail: %s' % output_thumbnail_filepath)
  return output_thumbnail_filepath


def get_pixels(dicom):
  log.info('Getting pixels for in DICOM: %s' % dicom_path)

  # Guess a transfer syntax if none is available
  if 'TransferSyntaxUID' not in dicom.file_meta:
    dicom.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian  # 1.2.840.10008.1.2
    put_to_dicom_private_header(dicom, key='AssumedTransferSyntaxUID', value='pydicom.uid.ImplicitVRLittleEndian 1.2.840.10008.1.2', superkey='Image  ')
    log.warning('Assumed TransferSyntaxUID')

  # Get Pixels
  if not 'pixel_array' in dicom:
    img = dicom.pixel_array
  else:
    log.error('Pixel data not found in DICOM: %s' % filename)
    return

  # Image shape
  log.info('Got pixels of shape: %s TransferSyntaxUID: %s' % (str(img.shape), dicom.file_meta.TransferSyntaxUID))
  if len(img.shape) not in [2,3]:
    # TODO: Support 3rd physical dimension, z-slices. Assuming dimenions x,y,[color] from here on.
    log.warning('Skipping image becasue shape is not 2d-grey or rgb: %s' % filename)
    return
  if len(img.shape) == 3 and img.shape[2] != 3:
    log.warning('Skipping image becasue shape is z-stack: %s' % filename)
    return

  # Crop the image to 100x100 just for fast algorithm testing
  if args.fast_crop:
    log.warning('Cropping image to 100x133')
    img = img[0:100, 0:133]

  # Colorspace
  img = convert_colorspace(img, dicom)
  
  img_orig = img

  # Convert to greyscale
  if len(img.shape) == 3:
    image = Image.fromarray(img,'RGB')
    image = image.convert('L')
    img = np.array(image)

  if args.screen:
    fig, ax = plt.subplots()
    ax.set_title('Original')
    im = ax.imshow(img, vmin=None, vmax=None) # https://matplotlib.org/3.1.0/api/_as_gen/matplotlib.pyplot.imshow.html
    ax.axis('off')
    # plt.show(block=False)

  return (img, img_orig, dicom) # return greyscale image and original rgb image

def flatten(l):
  for el in l:
    if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
      yield from flatten(el)
    else:
      yield el

def tophat_proprocess(img):

  # Unsharp (sharpen)
  img = cv2.GaussianBlur(img, (9,9), 10.0)
  gaussian_3 = cv2.GaussianBlur(img, (9,9), 10.0)
  img = cv2.addWeighted(img, 1.5, gaussian_3, -0.5, 0, img)
  img = cv2.addWeighted(img, 1.5, gaussian_3, -0.5, 0, img)
  img = cv2.addWeighted(img, 1.5, gaussian_3, -0.5, 0, img)
  # img = cv2.addWeighted(img, 1.5, gaussian_3, -0.5, 0, img)
  # img = cv2.addWeighted(img, 1.5, gaussian_3, -0.5, 0, img)

  # image = Image.fromarray(img,'L')
  # # Blur
  # image = image.filter( ImageFilter.GaussianBlur(radius=3))
  # # Sharpen Edges a Lot
  # image = image.filter( ImageFilter.EDGE_ENHANCE_MORE )
  # img = np.array(image)

  if args.screen:
    fig, ax = plt.subplots()
    ax.set_title('Blur Sharpen Preprocess')
    im = ax.imshow(img, vmin=None, vmax=None) # https://matplotlib.org/3.1.0/api/_as_gen/matplotlib.pyplot.imshow.html
    ax.axis('off')
    # plt.show()

  # TopHat to strengthen text
  img = white_tophat(img, disk(10))
  img = white_tophat(img, disk(10))
  # img = opening(img, disk(1))

  img = cv2.GaussianBlur(img, (9,9), 10.0)

  # if screen:
  #   fig, ax = plt.subplots()
  #   ax.set_title('TopHat Preprocess')
  #   im = ax.imshow(img, vmin=None, vmax=None) # https://matplotlib.org/3.1.0/api/_as_gen/matplotlib.pyplot.imshow.html
  #   ax.axis('off')
  #   plt.show()

  return img

def blur_sharpen_preprocess(img):
  image = Image.fromarray(img,'L')
  # Blur
  image = image.filter( ImageFilter.GaussianBlur(radius=1.5))
  # Sharpen Edges a Lot
  image = image.filter( ImageFilter.EDGE_ENHANCE_MORE )
  img = np.array(image)
  return img

def get_PHI():
  """ Note: there may be more PHI values than keys because we split name into several values and look for each seperately """
  PHI = list(found_PHI.values())
  
  if len(PHI) == 0:
    return []

  # Split by whitespace or '^' PatientName is typically: FirstName^LastName
  parts = [re.split('\^|\s',x) for x in PHI]
  PHI.extend(flatten(parts))

  # Ensure upper case
  PHI = [x.upper() for x in PHI if x is not None]

  # Remove whitespace only elements
  PHI = [x for x in PHI if x.strip() is not '']

  # Remove PHI that is less than 3 characters
  PHI = [x for x in PHI if len(x) > 2]

  # Remove PHI that is 3 characters and not entirely letters (not unique enough to allow, fuzzy matching will fail too often)
  parts = [x for x in PHI if re.match('^[a-zA-Z]..$', x)]
  [PHI.remove(x) for x in parts]

  # Unique
  PHI = list(set(PHI))

  # Sort alphabetically when numbers following letters
  PHI = sorted(PHI, key=lambda x: (x[0].isdigit(), x))

  return PHI

def ocr(img, ocr_num=None):
  log.info('Starting OCR...')
  tesseract_config = '--oem %d --psm 3' % ocr_num
  detection = pytesseract.image_to_data(img,config=tesseract_config, output_type=pytesseract.Output.DICT)
  detection = pd.DataFrame.from_dict(detection) # convert to dataframe
  detection = detection[[text.strip() != '' for text in detection.text]] # remove empty strings
  detection = detection.reset_index() # make sure index (row id) doesn't skip numbers
  log.info('Redacted %d instances of PHI from pixels' % len(detection))
  return detection

def ocr_match(search_strings, detection, ocr_num=None):
  """ Fuzzy matches strings or dates and returns results in pandas dataframe called "detection" which includes data about the location and confidence of matches in pixels """
  if detection.empty or search_strings is None or search_strings == []:
    return detection

  match_confs = [] # confidence
  match_texts = [] # closest match
  match_bool = [] # whether it's a positive match

  for i in range(0,len(detection)):
    text = detection.text.iloc[i]

    # Sanitize input
    valid_str = True
    if len(text) <= 2: # check that text is longer than two characters
      valid_str = False
    elif re.match('.*\w.*', text) is None: # check that text contains letter or number
      valid_str = False

    if valid_str:
      # Try fuzzy string matching
      heighest_match_conf = 0
      heighest_match_text = 0
      # Split detected text by whitespace and try to fuzzy match each word
      for word in text.split():
        match_text, match_conf = process.extractOne(word.upper(), search_strings, scorer=fuzz.ratio) # fuzzy match
        if match_conf > heighest_match_conf:
          heighest_match_conf = match_conf
          heighest_match_text = match_text
      if heighest_match_conf > MATCH_CONF_THRESHOLD:
        match_texts.append(match_text)
        match_confs.append(match_conf)
        match_bool.append(True)
        continue

      # Fall back to fuzzy date matching
      _match_text = datematcher(search_strings, text, fuzzy=True)
      if _match_text:
        match_texts.append(_match_text[0])
        match_confs.append(999) # no confidence given by datematcher
        match_bool.append(True)
        continue

    # Else add something to retain shape of datafram
    match_texts.append('')
    match_confs.append(0)
    match_bool.append(False)

  detection['match_text'] = match_texts
  detection['match_conf'] = match_confs
  detection['match_bool'] = match_bool

  return detection

def convert_image_numpy_to_pillow(img_np):
  img_dtype = str(img_np.dtype)
  # Work-around for Pillow which doesn't support 16bit images
  # https://github.com/python-pillow/Pillow/issues/2970
  if 'uint16' == img_dtype:
    cv2.normalize(img_np, img_np, 0, 255, cv2.NORM_MINMAX)
    # img_np = img_np.astype('uint16')
    # img_pillow = Image.fromarray(img_np)
    # image_PHI = Image.fromarray(img_np)
    array_buffer = img_np.tobytes()
    img_pillow = Image.new("I", img_np.T.shape)
    img_pillow.frombytes(array_buffer, 'raw', "I;16"
      )
  elif 'int16' == img_dtype:
    # Pillow fully doesn't support u16bit images! eek. TODO: Find a way to preserve 16 bit precision. I tried a bunch of stuff but couldn't preserve appearent constrast
    cv2.normalize(img_np, img_np, 0, 255, cv2.NORM_MINMAX)
    img_np = img_np.astype('uint16')
    array_buffer = img_np.tobytes()
    img_pillow = Image.new("I", img_np.T.shape)
    img_pillow.frombytes(array_buffer, 'raw', "I;16"
      )
  else:
    # Let Pillow Decide
    img_pillow = Image.fromarray(img_np)

  return img_pillow

def clean_pixels(dicom, detection):
  """ Put black boxes in image to "clean" it """
  if detection.empty or not any(detection.match_bool):
    log.warning('Nothing to clean')
    return

  dicom_pixels = dicom.pixel_array

  # Draw Detected Text Annotations
  for index, row in detection.iterrows():
    if not row.match_bool:
      continue

    global found_PHI_count_pixels
    found_PHI_count_pixels += 1

    # Black out in actual dicom pixels
    sml_left = int(row.left / RESIZE_FACTOR)
    sml_top = int(row.top / RESIZE_FACTOR)
    sml_width = int(row.width / RESIZE_FACTOR)
    sml_height = int(row.height / RESIZE_FACTOR)
    dicom_pixels[sml_top:sml_top+sml_height, sml_left:sml_left+sml_width] = 0
    dicom_pixels[sml_top, sml_left:sml_left+sml_width] = np.max(dicom_pixels)
    dicom_pixels[sml_top+sml_height, sml_left:sml_left+sml_width] = np.max(dicom_pixels)
    dicom_pixels[sml_top:sml_top+sml_height, sml_left] = np.max(dicom_pixels)
    dicom_pixels[sml_top:sml_top+sml_height, sml_left+sml_width] = np.max(dicom_pixels)

  # Store updated pixels in DICOM
  decompress_dicom(dicom)
  dicom.PixelData = dicom_pixels.tobytes()

def create_debug_images(dicom, img_orig, img_enhanced, detection, is_mostly_text, amount_of_text_score):
  """ Put black boxes in image to "clean" it """
  # Debug info
  if not args.screen and not args.gifs:
    return
  log.info('Creating debug images.')

  yellow = 'rgb(255, 255, 0)' # yellow color
  black = 'rgb(0, 0, 0)' # yellow input_color
  width = img_orig.shape[1]
  height = int(14*img_orig.shape[1]/120/RESIZE_FACTOR)+4
  left = 0
  top = img_orig.shape[0]-height
  xy = [left, top, left+width, top+height]
  choice_str = 'REJECT' if is_mostly_text else 'ACCEPT'
  filename = os.path.basename(dicom_path)
  metadata_fontsize = int(14*img_orig.shape[1]/200/RESIZE_FACTOR)
  img_dtype = str(img_orig.dtype)

  # For debugging purposes, image_PHI is the image with detected PHI overlaid annotations, draw_PHI is a helper object for annotating. It will be used in a gif. image_all_txt is the image with all detected text overlaid annotations, draw_all_txt is a helper object for annotating.
  image_orig = convert_image_numpy_to_pillow(img_orig)
  image_enhanced = convert_image_numpy_to_pillow(img_enhanced)
  image_PHI = image_orig.copy()
  draw_PHI = ImageDraw.Draw(image_PHI)
  image_all_txt = image_orig.copy()
  draw_all_txt = ImageDraw.Draw(image_all_txt)
  draw_enhanced_txt = ImageDraw.Draw(image_enhanced)

  # Draw boxes for each detected text annotations
  for index, row in detection.iterrows():
    # Black out pixels with debug info overlayed in boxes (for debugging only)
    annotation = 'ocr: %s, %d\nmatch: %s, %d' % (row.text, row.conf, row.match_text, row.match_conf)
    xy = [row.left, row.top, row.left+row.width, row.top+row.height]
    font = ImageFont.truetype('Roboto-Regular.ttf', size=int(row.height/2.5))
    draw_all_txt.rectangle(xy, fill=black, outline=yellow)
    draw_all_txt.multiline_text((row.left, row.top), annotation, fill=yellow, font=font)
    if row.match_bool:
      draw_PHI.rectangle(xy, fill=black, outline=yellow)
      draw_PHI.multiline_text((row.left, row.top), annotation, fill=yellow, font=font)

  # Write information in a bottom bar ontop of image
  annotation = ' %s, %d text score, %s, %s' % (filename, amount_of_text_score, img_dtype, choice_str)
  font = ImageFont.truetype('Roboto-Regular.ttf', size=metadata_fontsize)
  draw_PHI.rectangle(xy, fill=black, outline=yellow)
  draw_PHI.multiline_text((left, top), ' PHI' + annotation, fill=yellow, font=font, align='left')
  draw_all_txt.rectangle(xy, fill=black, outline=yellow)
  draw_all_txt.multiline_text((left, top), ' ALL' + annotation, fill=yellow, font=font, align='left')
  draw_enhanced_txt.rectangle(xy, fill=black, outline=yellow)
  draw_enhanced_txt.multiline_text((left, top), ' ENHANCED' + annotation, fill=yellow, font=font, align='left')

  # Create an image with all available PHI listed in the image
  image_PHI_list = Image.new(image_orig.mode, image_orig.size)
  spacing = metadata_fontsize / 2
  draw_PHI_list = ImageDraw.Draw(image_PHI_list)
  for pii in get_PHI():
    draw_PHI_list.multiline_text((metadata_fontsize / 2, spacing), pii, fill=yellow, font=font)
    spacing += 15 + metadata_fontsize

  # Display
  if args.screen:
    image_PHI.show()
    plt.show()
  if args.gifs:
    # Make Gif
    gif_filepath = '%s.gif' % output_debug_filepath
    image_orig = image_orig.convert('RGB')
    image_PHI = image_PHI.convert('RGB')
    image_all_txt = image_all_txt.convert('RGB')
    frames = [image_all_txt, image_PHI, image_enhanced, image_orig, image_PHI_list]
    frames[0].save(gif_filepath, format='GIF', append_images=frames[1:], save_all=True, duration=2222, loop=0)
    log.info('Saved debug GIF: %s' % gif_filepath)
    # Make Montage
    montage_filepath = '%s.montage.gif' % output_debug_filepath
    montage = make_image_montage(frames)
    montage.save(montage_filepath, format='gif')
    log.info('Saved debug montage: %s' % montage_filepath)

    if args.display_gif:
      # Open the gif for the user to see
      from subprocess import Popen
      p = Popen(["eog",gif_filepath])
      p = Popen(["eog",montage_filepath])

def make_image_montage(images):
  rows = 2
  widths, heights = zip(*(i.size for i in images))
  columns = math.ceil(len(images) / rows)
  max_width = max(widths)
  max_height = max(heights)
  total_width = max_width * columns
  total_height = max_height * rows
  new_img = Image.new('RGB', (total_width, total_height))
  for idx in range(rows):
    y_offset = idx*max_height
    image_subset = images[idx*columns:idx*columns+(columns)] # just images in this row
    x_offset = 0
    for img in image_subset:
      new_img.paste(img, (x_offset,y_offset))
      x_offset += img.size[0]
  return new_img

def decompress_dicom(dicom):
  if dicom.file_meta.TransferSyntaxUID.is_compressed:
    try:
      dicom.decompress()
    except:
      log.warning('Failed to decompress dicom.')

def remove_big_small_text(detection, img_shape):
  """ Remove detected text that has a height of greater 15% of image or less than 0.5% of image. """
  drop_idx = []
  img_height = img_shape[0]
  for index, text in detection.iterrows():
    text_height_as_percent_of_image = text.height / img_height
    if text_height_as_percent_of_image < 0.005 or text_height_as_percent_of_image > 0.15:
      drop_idx.append(index)
  detection = detection.drop(detection.index[drop_idx]) # remove row
  return detection

def amount_of_edges(img):
  # Unshap (sharpen)
  gaussian_3 = cv2.GaussianBlur(img, (9,9), 10.0)
  img = cv2.addWeighted(img, 1.5, gaussian_3, -0.5, 0, img)
  img = cv2.addWeighted(img, 1.5, gaussian_3, -0.5, 0, img)

  if args.screen:
    fig, ax = plt.subplots()
    ax.set_title('Canny preprocess')
    im = ax.imshow(img, vmin=None, vmax=None) # https://matplotlib.org/3.1.0/api/_as_gen/matplotlib.pyplot.imshow.html
    ax.axis('off')

  # Edge Detect
  img = feature.canny(img, sigma=.01)
  percent_edge = np.sum(img) / img.size # percentage of pixels which are detected to be edges

  print(percent_edge)
  print(percent_edge)
  print(percent_edge)
  print(percent_edge)
  print(percent_edge)

  if args.screen:
    fig, ax = plt.subplots()
    ax.set_title('Canny')
    im = ax.imshow(img, vmin=None, vmax=None) # https://matplotlib.org/3.1.0/api/_as_gen/matplotlib.pyplot.imshow.html
    ax.axis('off')
    plt.show()

  return percent_edge

def amount_of_text(detection):
  num_pixels = 123913
  # Score amount of text
  # the amount of text is scored by multiply the number of characters by the confidence of the detected text block
  score = 0
  for index, row in detection.iterrows():
    score += row.conf*len(row.text)
  score = score / (num_pixels / 1000) # divide by number of pixels (divided by a thousand cause number of pixels is really large and I'm worried about losing precision, so make smaller)

  # Check if amount of text is greater than threshol and so must come before other de-identificationd
  is_mostly_text = False
  if score > TOO_MUCH_TEXT_THRESHOLD:
    is_mostly_text = True

  return (is_mostly_text, score)

def process_pixels(dicom):
  # Get Pixels
  ret = get_pixels(dicom)
  if ret is None:
    return

  img_bw, img_orig, dicom = ret

  # Upscale image to improve OCR
  img_bw = cv2.resize(img_bw, dsize=(int(img_bw.shape[1]*RESIZE_FACTOR), int(img_bw.shape[0]*RESIZE_FACTOR)), interpolation=cv2.INTER_CUBIC)
  img_orig = cv2.resize(img_orig, dsize=(int(img_orig.shape[1]*RESIZE_FACTOR), int(img_orig.shape[0]*RESIZE_FACTOR)), interpolation=cv2.INTER_CUBIC)

  # Skip if image is too large (this just takes too long)
  if img_bw.size > MAX_NUM_PIXELS:
    log.warning('Couldnt read pixels so skipping: %s' % dicom_path)

  # Triage for text. Count number of egdes, if few edges then OCR is not needed so return early.
  # log.info('Triaging for text...')

  # img = img_bw
  # gaussian_3 = cv2.GaussianBlur(img, (9,9), 10.0)
  # img = cv2.addWeighted(img, 1.5, gaussian_3, -0.5, 0, img)
  # img = cv2.addWeighted(img, 1.5, gaussian_3, -0.5, 0, img)
  
  # is_mostly_text, amount_of_text_score = amount_of_text(ocr(tophat_proprocess(img), ocr_num=2))
  # print('is_mostly_text, amount_of_text_score: %s, %s' % (is_mostly_text, amount_of_text_score))
  # percent_edge = amount_of_edges(img_bw)
  # return


  # Preprocess Pixels (Variety #1)
  log.info('Processing 1...')
  img_enhanced = tophat_proprocess(img_bw)

  # Detect Text with OCR
  detection = ocr(img_enhanced, ocr_num=2)

  # Detect if image has so much text that it's probably a requisition and should be rejected or so little text that it should be accepted without PHI matching


  detection = remove_big_small_text(detection, img_bw.shape)

  # Score if this image has too much text
  is_mostly_text, amount_of_text_score = amount_of_text(detection)

  # Match Detected Text to PHI
  log.info('Matching 1...')
  detection = ocr_match(get_PHI(), detection, ocr_num=2)

  if args.ocr_fallback_enabled:
    # Preprocess Pixels (Variety #2)
    log.info('Processing 2...')
    img_enhanced = blur_sharpen_preprocess(img_bw)

    # Detect Text with OCR
    detection2 = ocr(img_enhanced, ocr_num=2)

    # Match Detected Text to PHI
    log.info('Matching 2...')
    detection2 = ocr_match(get_PHI(), detection2, ocr_num=2)

    # Combine detection results of different preprocessing
    detection = pd.concat([detection, detection2], ignore_index=True, sort=True)

  # Clean Image Pixels
  clean_pixels(dicom, detection)

  # Display Debug Images
  create_debug_images(dicom, img_orig, img_enhanced, detection, is_mostly_text, amount_of_text_score)

  return True

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
      log.error('linking index does not exist!')
    else:
      raise e
  return res

def insert_dicom_into_elastic(dicom):
  if not args.save_to_elastic:
    return

  dicom_metadata = dicom_to_dict(dicom, log=log, environ=ENVIRON)

  dicom_metadata['dicom_filename'] = os.path.basename(output_image_filepath)
  dicom_metadata['dicom_filepath'] = output_image_filepath
  dicom_metadata['dicom_webpath'] = output_image_webpath
  dicom_metadata['thumbnail_filename'] = os.path.basename(output_thumbnail_filepath)
  dicom_metadata['thumbnail_filepath'] = output_thumbnail_filepath
  dicom_metadata['thumbnail_webpath'] = output_thumbnail_webpath
  if 'PatientAge' in dicom:
    dicom_metadata['PatientAgeInt'] = float(dicom.get('PatientAge'))
  dicom_metadata['original_title'] = 'Dicom'
  dicom_metadata['searchallblank'] = '' # needed to search across everything (via searching for empty string)

  res = es.index(body=dicom_metadata, index=INDEX_NAME, doc_type=DOC_TYPE)

  if res['result'] == 'created':
    log.info('Inserted de-identified dicom into ElasticSearch')
  else:
    log.error('Insert de-identified report into ElasticSearch FAILED.')
    log.error('elasticsearch index result = %s' % res)

def get_report_from_dicom(dicom, return_only_key_values=False):
  metadata = get_private_metadata_as_dict(dicom)
  if 'Report ' in metadata:
    return
  report =  metadata['Report ']

  # Optionally exclude dicom tags
  if return_only_key_values:
    kv_report = {}
    for key in report.keys():
      kv_report[key] = report[key]['value']
    report = kv_report

  return report

def get_report_from_elastic(AccessionNumber):
  if not AccessionNumber:
    return

  # Lookup report by AccessionNumebr
  result = es.search(
    index=REPORT_INDEX_NAME,
    doc_type=REPORT_DOC_TYPE,
    size=1,
    body={'query': {'term': {'Accession Number.keyword': AccessionNumber}}}
  )

  if result['hits']['total'] == 0:
    log.info('No report found in ElasticSearch for AccessionNumber: %s' % AccessionNumber)
    return

  report = result['hits']['hits'][0]['_source']
  report['id'] = result['hits']['hits'][0]['_id']

  log.info('Found report: %s' % report['filepath'])

  return report

def insert_deid_report_into_elastic(dicom):
  if not args.save_to_elastic:
    return

  report = get_report_from_dicom(dicom, return_only_key_values=True)
  
  if not report:
    log.warning('No report associated with DICOM, so not saving deid report to elastic')
    return

  # Don't Insert into ElasticSearch if already there
  result = es.search(
    index=DEID_REPORT_INDEX_NAME,
    doc_type=DEID_REPORT_DOC_TYPE,
    size=1,
    body={'query': {'term': {'AccessionNumber.keyword': dicom.get('AccessionNumber')}}}
  )

  if result['hits']['total'] > 0:
    log.warning("Not inserting deid report into ElasticSearch because it already exists.")
    return

  # Create report data structure
  report['original_title'] = 'Report'
  report['searchallblank'] = '' # needed to search across everything (via searching for empty string)

  # Insert
  res = es.index(body=report, index=DEID_REPORT_INDEX_NAME, doc_type=DEID_REPORT_DOC_TYPE)

  if res['result'] == 'created':
    log.info('Inserted de-identified report into ElasticSearch')
  else:
    log.error('Insert de-identified report into ElasticSearch FAILED.')
    log.error('elasticsearch index result = %s' % res)

def generate_uid(dicom_dict, function_name=None, field_name=None):
  """ This function generates a uuid to put in place of PHI and trackes the linking between UUID and PHI by inserting into ElasticSearch """
  orig = dicom_dict[field_name] if field_name in dicom_dict else ''
  if orig == '':
    return ''

  global found_PHI_count_header
  found_PHI_count_header += 1

  # Look to find existing linking in ElasticSearch
  if args.save_to_elastic:
    res = lookup_linking(orig)

    if len(res):
      # Found existing in elastic, use id already generated
      uid = res[0]['_source']['new']
    else:
      uid = str(uuid.uuid4()) # otherwise generate new id
      # otherwise insert a new linking for this unseen original value to a uid
      query = {'orig': orig, 'new': uid, 'field': field_name, 'date': datetime.datetime.now(), 'orig_path': dicom_dict['orig_path'], 'new_path': dicom_dict['new_path']}
      if '_id' in dicom_dict:
        query['id'] = dicom_dict['_id'] # Use same elasticsearch document ID from input index in the new index
      res = es.index(body=query, index=LINKING_INDEX_NAME, doc_type=LINKING_DOC_TYPE)

    log.debug('Linking %s:%s-->%s' % (field_name, orig, uid))

  # Keep track of what PHI was found
  found_PHI[field_name] = orig

  return uid

def extract_key_value_from_field(field):
  seperate_key_value = str(field.value).split(": ")
  superkey = seperate_key_value[0][:7]
  key = seperate_key_value[0][7:].strip()
  value = ":".join(seperate_key_value[1:]) #7 means the end of the word "report"
  return superkey, key, value

def get_private_metadata_as_dict(dicom):
  metadata = {}
  tag = [0x0019, 0x0030]
  metadata_part = dicom.get(tag)

  while(metadata_part is not None):
    superkey, key, value = extract_key_value_from_field(metadata_part)
    if superkey not in metadata: metadata[superkey] = {}
    if key not in metadata[superkey]: metadata[superkey][key] = {}
    metadata[superkey][key]['value'] = value
    metadata[superkey][key]['tag'] = tag

    # Increment to next field in the report section of the dicom header
    tag[1] += 1
    metadata_part = dicom.get(tag)

  return metadata


def datematcher(possibly_dates, text, fuzzy=False):
  """
  @param possibly_dates: a list of strings of dates
  @param text: the block of text that will be searched for dates
  @return Returns dates exactly as found in text that match dates in input possibly_dates

  TODO (low priority): Explore enabling parser.parse(fuzzy=true) in: /usr/local/lib/python3.5/dist-packages/datefinder/__init__.py
  https://dateutil.readthedocs.io/en/stable/parser.html#dateutil.parser.parse
  """
  found_dates = []
  returning = set()

  found_dates_dfinder = datefinder.find_dates(str(text), source=True) #finds all dates in text using datefinder
  found_dates_dfinder = list(found_dates_dfinder)
  found_dates.extend(found_dates_dfinder) #add all the dates found from datefinder to the master list of dates

  found_dates_dparser = search_dates(str(text)) #finds all dates in text using dateparser
  if found_dates_dparser:
    found_dates_dparser = list(found_dates_dparser)
    for dp_date in found_dates_dparser: #add all the dates found from dateparser to the master list of dates in the correct order as a tuple with the datefinder object first and the part of the text that the date was found in
      found_dates.append((dp_date[1], dp_date[0]))

  for datetime_object in possibly_dates:
    for found_date in found_dates:
      found_date = {
        'object' : found_date[0],
        'string' : found_date[1],
      }
      if datetime_object == found_date['object']: #if the date matches one that was in input text
        returning.add(found_date['string']) #append the line of text where the dates matched

      elif fuzzy: #not an exact match so should check if it is a fuzzy match
        date_string = datetime_object.strftime('%Y%m%d')
        found_date_string = found_date['object'].strftime('%Y%m%d')
        # The >=75 allows for two different digit swaps assuming 8 characters. And the >=5 confirms that the date is long enough to be an actual date not just a short string of random numbers. And the !=today() ignores "found" dates that match todays date because datefinder assumes today's date if there is missing date information
        if fuzz.ratio(date_string, found_date_string) >= 75 and len(found_date['string']) >= 5 and found_date['object'].date() != datetime.datetime.today().date():
          returning.add(found_date['string'])

  return list(returning)

def match_and_replace_PHI(dicom, field_tag, fuzzy=False):
  """ Finds and replaces PHI in inplace in DICOM be it a date or an exact string match with a UUID."""
  field = dicom.get(field_tag)

  # Skip certain tags # TODO: choose more that shouldn't contain PHI
  short_name = field.name.replace(' ','') # pydicom gives field names with spaces while deid.recipe doesn't have spaces
  if short_name in cleaned_tag_names_list:
    return
  # Skip values less than 3 characters
  if len(str(field.value)) <= 3:
    return

  PHI_notdates = []
  PHI_dateobjects = []


  if (field != None): #check if the field exists
    PHI = get_PHI() #get all PHI values so far

    # PHI.append("2034.06.20")
    # PHI.append("2035/02/15")
    # PHI.append("PFIRST")
    # PHI.append("PLAST")

    if not PHI:
      return

    # Sort PHI into two lists: Dates and Not Dates
    for element in PHI:
      element_dt_obj = datefinder.find_dates(element)
      element_dt_obj = list(element_dt_obj)
      if element_dt_obj == []:
        PHI_notdates.append(element)
      else:
        PHI_dateobjects.extend(element_dt_obj)

    # Update DICOM
    try:
      #replace exact matches with UID
      value = match_and_replace_exact(dicom, field_tag, PHI_notdates)
      if str(value) != str(field.value): # only if a replacement was made
        field.value = value
        dicom[field.tag] = pydicom.DataElement(field.tag, field.VR, field.value) # set back into dicom

      #replace possible date matches that aren't directly in text with UID
      value = match_and_replace_dates(dicom, field_tag, PHI_dateobjects, fuzzy)
      if str(value) != str(field.value): # only if a replacement was made
        field.value = value
        dicom[field.tag] = pydicom.DataElement(field.tag, field.VR, field.value) # set back into dicom
    except Exception as e:
      print(traceback.format_exc())
      log.error('Failed to set dicom field "%s" with value "%s". The original value will remain in place without any redaction.' % (field, value))

def match_and_replace_exact(dicom, field_tag, PHI):
  """matches and replaces PHI dates that were the exact same format as those found in the specified field
  Returns the updated field of the dicom"""
  dicom_field = dicom.get(field_tag)
  field_val = dicom_field.value

  for element in PHI:
    if element.upper() in str(field_val).upper():
      if len(element) >= 3: #is not a date but is an exact match
        _dict = {dicom_field.name: element, 'new_path': output_image_filepath, 'orig_path': dicom_path}
        UID = generate_uid(_dict, field_name=dicom_field.name)
        field_val = field_val.replace(element, str(UID))

  return field_val

def match_and_replace_dates(dicom, field_tag, PHI_dateobjects, fuzzy=False):
  """matches and replaces PHI dates that were not the exact same format as those found in the specified field
  Returns the updated field of the dicom"""
  dicom_field = dicom.get(field_tag) 
  field_val = str(dicom_field.value)

  # To speed up computation don't try to match dates if we can till it's not going to be a date.
  # Skip if not 2 or more numbers
  if not re.match('.*[0-9].*[0-9].*', field_val.replace('\n','')):
    return
  # Skip if is UUID
  try:
    if isinstance(uuid.UUID(field_val), uuid.UUID):
      return
  except:
    # if it's not a UUID, check it for a date
    pass

  found_date_strings = datematcher(PHI_dateobjects, field_val, fuzzy) #get all dates from the specified field of the dicom

  for found_date in found_date_strings: #check where the date is and replace it 
  # Split found date string into parts because sometimes we over detect and include words like "on" so we'll next loop over the parts looking for the just the date to replace
    split_day = re.split('[ :]', found_date)
    for split_piece in split_day:
      split_dt_obj = datefinder.find_dates(split_piece, source= True)
      split_dt_obj = list(split_dt_obj)

      if split_dt_obj != []: #if a date was found
        _dict = {dicom_field.name: split_dt_obj[0][0].strftime('%Y/%m/%d'), 'new_path': output_image_filepath, 'orig_path': dicom_path}
        UID = generate_uid(_dict, field_name=dicom_field.name)
        field_val = field_val.replace(split_dt_obj[0][1], str(UID))

  return field_val

def save_dicom_to_disk(dicom):
  try:
    dicom.save_as(output_image_filepath)
    log.info('Saved DICOM: %s' % output_image_filepath)
  except Exception as e:
    print(traceback.format_exc())
    log.error('Failed to save de-identified dicom to disk: %s\n' % output_image_filepath)
    if 'Pixel Data with undefined length must start with an item tag' in str(e):
      dicom[(0x7fe0,0x0010)].is_undefined_length = False
      dicom.save_as(output_image_filepath)
      log.error('Successfully recovered from error and saved de-identified dicom to disk: %s\n' % output_image_filepath)


def save_deid_report_to_disk(dicom):
  """save the edited file to the specified file given in the dicom. Also saves location of de-id'd report into dicom."""
  report = get_report_from_dicom(dicom)

  if not report:
    log.warning('No report associated with DICOM, so not saving deid report to disk')
    return

  if not os.path.exists(output_report_filepath):
    file_to_write = open(output_report_filepath, 'w')
    file_to_write.write(str(report['Raw']['value']))
    file_to_write.close()
    log.info('Saved de-identified report to disk: %s' % output_report_filepath)
  else:
    log.warning('Not saving de-identified report to disk because it already exists.')

  ## Save report filepath in DICOM header
  # Make copy of the old filepath (before de-identification)
  put_to_dicom_private_header(dicom, key='filepath_orig', value=input_report_filepath, superkey='Report ')
  # # Save the new filepath
  put_to_dicom_private_header(dicom, key='filepath', value=output_report_filepath, superkey='Report ')

def put_to_dicom_private_header(dicom, key=None, tag=None, value=None, superkey=None):
  """ Add new report data in dicom metadata """
  if not key:
    raise Exception('put_to_dicom_private_header() requires a key')
  if len(superkey) > 7:
    raise Exception('Currently only supporting superkeys that are 7 chars long, such as "Report " or "Image  ".')

  dicom_datatype = 'LT' # Dicom datatype Value Representation

  if key:
    loc_group = 0x0019
    loc_element = 0x0030
    loc = (loc_group, loc_element)

    # Remove all non-word characters (everything except numbers and letters)
    key = re.sub(r"[^\w\s]", '', key)
    key = re.sub(r"\s+", '', key)

    # Loop until the key is found in header or a free location for metadata is found in header
    while loc in dicom:
      # Check if we found key
      field = dicom[loc]
      a_superkey, a_key, a_value = extract_key_value_from_field(field)
      if key == a_key and superkey == a_superkey:
        break

      # Increment to use higher index on next loop
      loc_element = loc_element + 1 
      loc = (loc_group, loc_element)

  elif tag:
    loc = tag

  # Add new value
  value = "%s%s: %s" % (superkey, key, str(value)) # Append key name to start of value because dicom uses hexadecimal instead of key names
  dicom[loc] = pydicom.DataElement(loc, dicom_datatype, value)

def is_requisition(dicom):
  if 'SeriesNumber' in dicom:
    if re.match('^9+$', str(dicom.SeriesNumber)):
      return True
  return False

def add_audit_to_dicom(dicom):
  this_code = 'https://github.com/aim-sk/aim-platform/blob/196c9f19bb5ed99124001951c2343658f3a16b0a/image-archive/de-id/deid_dicoms.py'
  value = get_private_metadata_as_dict(dicom).get('ProcessingAudit')
  if value:
    value = value + ', ' + this_code
  else:
    value = this_code
  put_to_dicom_private_header(dicom, key='ProcessingAudit', value=value, superkey='Image  ')

def add_uuid(dicom):
  uid = str(uuid.uuid4())
  put_to_dicom_private_header(dicom, key='UUID', value=uid, superkey='Image  ')
  return uid

def add_report(dicom, report):
  """Add report into dicom header"""
  if not report:
    return

  # Add new data in dicom report
  for key, value in report.items():
    put_to_dicom_private_header(dicom, key=key, value=value, superkey='Report ')
  put_to_dicom_private_header(dicom, key='webpath', value=output_report_webpath, superkey='Report ')

def already_cleaned_tag_names():
  with open(args.deid_recipe, 'r') as f:
    names = f.read().split('\n')
    names = [line.split()[1] for line in names if 'REPLACE' in line] # convert "REPLACE AdmissionID func:generate_uid" to "AdmissionID"
    return names

def iter_simple_fields(dicom):
  for field in dicom.iterall():
    # Skip pixel data
    if field.name == 'Pixel Data':
      continue
    # Skip objects of this kind because they can't be made into strings, perhaps go deeper
    if field.value.__class__ in [pydicom.sequence.Sequence, pydicom.valuerep.PersonName3, pydicom.multival.MultiValue, pydicom.valuerep.DSfloat, pydicom.valuerep.IS, int]:
      continue
    yield field

def deidentify_header(dicom):
  # Prepare to De-Identify Metadata
  log.info('De-identifying DICOM header...')
  recipe = DeidRecipe(args.deid_recipe) # de-id rules
  dicom_dict = get_identifiers([dicom_path])
  dicom_dict[dicom_path]['new_path'] = output_image_filepath
  dicom_dict[dicom_path]['orig_path'] = dicom_path
  dicom_dict[dicom_path]['generate_uid'] = generate_uid # Remember, the action found in deid.recipe is "REPLACE StudyInstanceUID func:generate_uid" so the key here needs to be "generate_uid"

  # De-Identify Metadata (and keep track of value replacements ie. linking) (and this will populate the found_PHI global variable)
  cleaned_files = replace_identifiers(dicom_files=dicom_path,
                                      deid=recipe,
                                      ids=dicom_dict,
                                      save=False,
                                      remove_private=False)
                                      # overwrite=True,
                                      # output_folder=output_folder)

  log.info('Found %s unique pieces of PHI.' % len(found_PHI.keys()))
  cleaned_header_dicom = cleaned_files[0] # we only pass in one at a time
  # note: cleaned_header_dicom is not a full dicom. It is not as functional as the "dicom" variable

  # Copy from "cleaned_header_dicom" to "dicom" variable so that UUIDs take place of PHI. "dicom" is the preferred variable
  for key in found_PHI.keys():
    dicom.data_element(key).value = cleaned_header_dicom.data_element(key).value
    # Change VL data type from date to long string to try to get DWV to display it properly
    # NOTE: commented out because pydicom doesn't actually save the VL change
    
    # if dicom.data_element(key).VR in  ['DA','DT','TM']:
    #   dicom.data_element(key).VR = 'LO' # these fieldsa are now UUIDs and so their type should be long string LO
    #   dicom[cleaned_header_dicom.data_element(key).tag] = pydicom.DataElement(cleaned_header_dicom.data_element(key).tag, 'LO', cleaned_header_dicom.data_element(key).value) # set back into dicom

  # Look for detected PHI in all DICOM fields and replace with UUIDs (this will de-id the report if present in the DICOM)
  for field in iter_simple_fields(dicom):
    match_and_replace_PHI(dicom, field.tag)

  log.info('Redacted %s instances of PHI from header and report' % found_PHI_count_header)

def store_number_of_redacted_PHI(dicom_uuid):
  """Record how many PHI was found and replaced in ElasticSearch"""
  query = {'type': 'pixel_PHI', 'count': found_PHI_count_pixels, 'uuid': dicom_uuid}
  res = es.index(body=query, index=COUNT_INDEX_NAME, doc_type=COUNT_DOC_TYPE)
  query = {'type': 'header_PHI', 'count': found_PHI_count_header, 'uuid': dicom_uuid}
  res = es.index(body=query, index=COUNT_INDEX_NAME, doc_type=COUNT_DOC_TYPE)

def setup_args():
  parser.add_argument('--output_folder', help='Save processed DICOM files to this path.')
  parser.add_argument('--output_folder_suffix', help='Add this folder to the output path and webpath.')
  parser.add_argument('--input_range', help='Positional document numbers in ElasticSearch (ex. 1-10). These documents will be processed.')
  parser.add_argument('--input_filelist', help='Pass in file that contains list of DICOM files which will be processed.')
  parser.add_argument('--input_file', help='Pass in a single DICOM file by giving path on disk.')
  parser.add_argument('--input_folder', help='Pass a folder containing DICOMs.')
  parser.add_argument('--input_base_path', help='Ignore this part of the input path when creating output folders.')
  parser.add_argument('--input_report_base_path', help='Ignore this part of the report input path when creating output folders.')
  parser.add_argument('--no_elastic', action='store_true', help='Skip saving metadata to ElasticSearch.')
  parser.add_argument('--deid_recipe', default='deid.recipe', help='De-id rules.')
  parser.add_argument('--no_deidentify', action='store_true', help='Whether or not to perform de-identification.')
  parser.add_argument('--input_dicom_filename', help='Process only this DICOM by name (looked up in ElasticSearch)')
  parser.add_argument('--ocr_fallback_enabled', action='store_true', help='Only try one pass of OCR to find PHI')
  parser.add_argument('--fast_crop', action='store_true', help='Crop the image to 100x100 just for fast algorithm testing')
  parser.add_argument('--screen', action='store_true', help='Display output pixels on screen')
  parser.add_argument('--gifs', action='store_true', help='Save output pixels to gifs')
  parser.add_argument('--display_gif', action='store_true', help='Open the gif for the user to see')
  parser.add_argument('--wait', action='store_true', help='Wait for user to press enter after processing each dicom')

def log_settings():
  log.info("Settings: %s=%s" % ('output_folder', args.output_folder))
  log.info("Settings: %s=%s" % ('output_folder_suffix', args.output_folder_suffix))
  log.info("Settings: %s=%s" % ('input_base_path', args.input_base_path))
  log.info("Settings: %s=%s" % ('input_report_base_path', args.input_report_base_path))
  log.info("Settings: %s=%s" % ('input_dicom_filename', args.input_dicom_filename))
  log.info("Settings: %s=%s" % ('input_range', args.input_range))
  log.info("Settings: %s=%s" % ('input_filelist', args.input_filelist))
  log.info("Settings: %s=%s" % ('input_file', args.input_file))
  log.info("Settings: %s=%s" % ('input_folder', args.input_folder))
  log.info("Settings: %s=%s" % ('save_to_elastic', args.save_to_elastic))
  log.info("Settings: %s=%s" % ('deid_recipe', args.deid_recipe))
  log.info("Settings: %s=%s" % ('ocr_fallback_enabled', args.ocr_fallback_enabled))
  log.info("Settings: %s=%s" % ('fast_crop', args.fast_crop))
  log.info("Settings: %s=%s" % ('screen', args.screen))
  log.info("Settings: %s=%s" % ('gifs', args.gifs))
  log.info("Settings: %s=%s" % ('display_gif', args.display_gif))
  log.info("Settings: %s=%s" % ('ELASTIC_IP', ELASTIC_IP))
  log.info("Settings: %s=%s" % ('ELASTIC_PORT', ELASTIC_PORT))
  log.info("Settings: %s=%s" % ('INDEX_NAME', INDEX_NAME))
  log.info("Settings: %s=%s" % ('DOC_TYPE', DOC_TYPE))
  log.info("Settings: %s=%s" % ('LINKING_INDEX_NAME', LINKING_INDEX_NAME))
  log.info("Settings: %s=%s" % ('LINKING_DOC_TYPE', LINKING_DOC_TYPE))
  log.info("Settings: %s=%s" % ('COUNT_INDEX_NAME', COUNT_INDEX_NAME))
  log.info("Settings: %s=%s" % ('COUNT_DOC_TYPE', COUNT_DOC_TYPE))
  log.info("Settings: %s=%s" % ('REPORT_INDEX_NAME', REPORT_INDEX_NAME))
  log.info("Settings: %s=%s" % ('REPORT_DOC_TYPE', REPORT_DOC_TYPE))
  log.info("Settings: %s=%s" % ('DEID_REPORT_INDEX_NAME', DEID_REPORT_INDEX_NAME))
  log.info("Settings: %s=%s" % ('DEID_REPORT_DOC_TYPE', DEID_REPORT_DOC_TYPE))
  log.info("Settings: %s=%s" % ('ENVIRON', ENVIRON))
  log.info("Settings: %s=%s" % ('FILESERVER_IP', FILESERVER_IP))
  log.info("Settings: %s=%s" % ('FILESERVER_PORT', FILESERVER_PORT))
  log.info("Settings: %s=%s" % ('FILESERVER_TOKEN', FILESERVER_TOKEN))
  log.info("Settings: %s=%s" % ('FILESERVER_DICOM_PATH', FILESERVER_DICOM_PATH))
  log.info("Settings: %s=%s" % ('FILESERVER_THUMBNAIL_PATH', FILESERVER_THUMBNAIL_PATH))
  log.info("Settings: %s=%s" % ('MATCH_CONF_THRESHOLD', MATCH_CONF_THRESHOLD))
  log.info("Settings: %s=%s" % ('TOO_MUCH_TEXT_THRESHOLD', TOO_MUCH_TEXT_THRESHOLD))
  log.info("Settings: %s=%s" % ('RESIZE_FACTOR', RESIZE_FACTOR))
  log.info("Settings: %s=%s" % ('wait', args.wait))
  log.info("Settings: %s=%s" % ('no_deidentify', not args.no_deidentify))
  

if __name__ == '__main__':
  # Set up command line arguments
  parser = argparse.ArgumentParser(description='Looks up documents in ElasticSearch, finds the DICOM files, processes them, and saves a copy.')
  setup_args()
  args = parser.parse_args()
  args.save_to_elastic = not args.no_elastic
  log_settings()

  if args.save_to_elastic:
    es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])
    # Test ElasticSearch connection 
    if not es.indices.exists(index=INDEX_NAME):
      raise Exception("Could not connect to ElasticSearch or Index doesn't exist")
    
  # Get List of Dicoms from a file
  if args.input_filelist:
    fp = open(args.input_filelist) # Open file on read mode
    dicom_paths = fp.read().split("\n") # Create a list containing all lines
    fp.close() # Close file
    dicom_paths = list(filter(None, dicom_paths)) # remove empty lines
  # Lookup one input file from Elastic
  elif args.input_file:
    dicom_paths = [args.input_file]
  # Find dcms in a folder
  elif args.input_folder:
    dicom_paths = list(glob.iglob('%s/**/*.dcm' % args.input_folder, recursive=True))
  # Lookup one input file from Elastic
  elif args.input_dicom_filename:
    query = {
      "_source": ["_id", "dicom_filepath"],
      "query": {
        "term": {
          "dicom_filename.keyword": args.input_dicom_filename
        }
      }
    }
  # Lookup many input files from Elastic
  elif args.input_range:
    input_start, input_end = [int(i) for i in args.input_range.split('-')]
    size = input_end - input_start + 1
    query = {
      "_source": ["_id", "dicom_filepath"],
      "from": input_start,
      "size": size,
    }

  # Actually get documents from ElasticSearch
  if args.input_dicom_filename or args.input_range:
    results = es.search(body=query, index=INDEX_NAME)
    log.info("Number of Search Hits: %d" % len(results['hits']['hits']))
    results = results['hits']['hits']
    dicom_paths = [res['_source']['dicom_filepath'] for res in results]

  log.info("Number of input files: %d" % len(dicom_paths))
  t0 = time.time()

  # MAIN LOOP: Process each dicom
  for idx, dicom_path in enumerate(dicom_paths):
    log.info('Processing DICOM path: %s' % dicom_path)
    found_PHI = {}
    found_PHI_count_pixels = 0
    found_PHI_count_header = 0

    log.info('############')
    log.info('##  Open  ##')
    log.info('############')

    # Open DICOM
    dicom = pydicom.dcmread(dicom_path, force=True)

    # Skip DICOMs that are requisitions, identified by SeriesNumber:999*
    if is_requisition(dicom):
      log.warning('Skipping requisition: %s' % dicom_path)
      continue

    # Open Report
    report = get_report_from_elastic(dicom.get('AccessionNumber'))
    if not report:
      report  = get_report_from_dicom(dicom, return_only_key_values=True) # if not in elastic, check if alreadm

    # Create output folders and filepaths (this must come near the start so that things can be saved when needed) (expand ~, environment variables, and make absolute path)
    dicom_path = os.path.abspath(os.path.expanduser(os.path.expandvars(dicom_path))) # /home/dan/Favourite_Images/MRI/1795084_117225373.dcm
    args.output_folder = os.path.abspath(os.path.expanduser(os.path.expandvars(args.output_folder))) # /home/dan/aim-platform/image-archive/reactive-search/static/
    args.input_base_path = os.path.abspath(os.path.expanduser(os.path.expandvars(args.input_base_path))) # /home/dan/Favourite_Images/
    if args.input_base_path not in dicom_path:
      raise Exception('Error: Couldnt find "args.input_base_path" in "dicom_path". Please check your CLI arguments.')
    dicom_path_short = dicom_path.replace(args.input_base_path,'').lstrip('/') # MRI/1795084_117225373.dcm
    log.info('dicom_path = %s' % dicom_path)
    if args.output_folder_suffix:
      log.info('args.output_folder_suffix = %s' % args.output_folder_suffix)
      args.output_folder = os.path.join(args.output_folder, args.output_folder_suffix) # /home/dan/aim-platform/image-archive/reactive-search/static/deid/
    log.info('args.output_folder = %s' % args.output_folder)
    log.info('args.input_base_path = %s' % args.input_base_path)
    log.info('dicom_path_short = %s' % dicom_path_short)
    output_image_filepath = os.path.join(args.output_folder, 'image', dicom_path_short) # example: /home/dan/aim-platform/image-archive/reactive-search/static/deid/image/MRI/1795084_117225373.dcm
    output_debug_filepath = os.path.join(args.output_folder, 'debug', dicom_path_short) # example: /home/dan/aim-platform/image-archive/reactive-search/static/deid/debug/MRI/1795084_117225373.dcm
    output_thumbnail_filepath = os.path.join(args.output_folder, 'thumbnail', dicom_path_short) + '.png' # example: /home/dan/aim-platform/image-archive/reactive-search/static/deid/thumbnail/MRI/1795084_117225373.dcm.png
    output_image_webpath = os.path.join('image', dicom_path_short) # example: image/MRI/1795084_117225373.dcm
    output_debug_webpath = os.path.join('debug', dicom_path_short) # example: debug/MRI/1795084_117225373.dcm
    output_thumbnail_webpath = os.path.join('thumbnail', dicom_path_short) + '.png' # example: thumbnail/MRI/1795084_117225373.dcm.png
    if args.output_folder_suffix:
      output_image_webpath = os.path.join(args.output_folder_suffix, output_image_webpath) # example: deid/image/MRI/1795084_117225373.dcm
      output_debug_webpath = os.path.join(args.output_folder_suffix, output_debug_webpath) # example: deid/debug/MRI/1795084_117225373.dcm
      output_thumbnail_webpath = os.path.join(args.output_folder_suffix, output_thumbnail_webpath) # example: deid/thumbnail/MRI/1795084_117225373.dcm.png
    log.info('output_image_filepath = %s' % output_image_filepath)
    log.info('output_debug_filepath = %s' % output_debug_filepath)
    log.info('output_thumbnail_filepath = %s' % output_thumbnail_filepath)
    log.info('output_image_webpath = %s' % output_image_webpath)
    log.info('output_debug_webpath = %s' % output_debug_webpath)
    log.info('output_thumbnail_webpath = %s' % output_thumbnail_webpath)
    output_image_folder = os.path.dirname(output_image_filepath)
    output_debug_folder = os.path.dirname(output_debug_filepath)
    output_thumbnail_folder = os.path.dirname(output_thumbnail_filepath)
    if not os.path.exists(output_image_folder):
      os.makedirs(output_image_folder)
    if not os.path.exists(output_debug_folder):
      os.makedirs(output_debug_folder)
    if not os.path.exists(output_thumbnail_folder):
      os.makedirs(output_thumbnail_folder)
    if report:
      args.input_report_base_path = os.path.abspath(os.path.expanduser(os.path.expandvars(args.input_report_base_path))) # example: /home/dan/aim-platform/image-archive/reports
      embed()
      input_report_filepath = os.path.abspath(os.path.expanduser(os.path.expandvars(report['filepath']))) # example: /home/dan/aim-platform/image-archive/reports/sample/Report_55123.txt
      if args.input_report_base_path not in input_report_filepath:
        raise Exception('Error: Couldnt find "args.input_report_base_path" in "input_report_filepath". Please check your CLI arguments.')
      report_path_short = input_report_filepath.replace(args.input_report_base_path,'').lstrip('/') # example: sample/Report_55123.txt
      output_report_filepath = os.path.join(args.output_folder, 'report', report_path_short) # example: /home/dan/aim-platform/image-archive/reactive-search/static/deid/report/sample/Report_55123.txt
      output_report_webpath = os.path.join('report', report_path_short) # example: report/sample/Report_55123.txt
      output_report_folder = os.path.dirname(output_report_filepath)
      if not os.path.exists(output_report_folder):
        os.makedirs(output_report_folder)
      log.info('args.input_report_base_path = %s' % args.input_report_base_path)
      log.info('input_report_filepath = %s' % input_report_filepath)
      log.info('report_path_short = %s' % report_path_short)
      log.info('output_report_filepath = %s' % output_report_filepath)

    log.info('##############')
    log.info('##  Enrich  ##')
    log.info('##############')

    # Add derived fields (must happen before de-identification since that could remove needed data)
    add_derived_fields(dicom)
    
    # Add report
    add_report(dicom, report)
    
    # Add UUID
    uid = add_uuid(dicom)

    # Record where the original DICOM file came from before it was de-identified
    put_to_dicom_private_header(dicom, key='filepath_orig', value=dicom_path, superkey='Image  ')
    
    # Record what code touched the image
    add_audit_to_dicom(dicom)

    if not args.no_deidentify:
      log.info('###################')
      log.info('##  De-Identify  ##')
      log.info('###################')

      # Store cleaned tag names so that they can be skipped at later times for faster performance
      cleaned_tag_names_list = already_cleaned_tag_names()

      # De-Identify Metadata (including report) (and keep track of value replacements ie. linking) (and this will populate the found_PHI global variable and so must come before other de-identification)
      deidentify_header(dicom)

      # Record how many PHI was found and replaced in ElasticSearch
      store_number_of_redacted_PHI(uid)

      # Process pixels (de-id pixels and save debug gif)
      result = process_pixels(dicom)
      if result is None:
        log.warning('Couldnt read pixels so skipping: %s' % dicom_path)
        continue

    log.info('############')
    log.info('##  Save  ##')
    log.info('############')

    # Save de-identified radiology report (if present) to disk
    save_deid_report_to_disk(dicom)

    # Insert de-identified report into ElasticSearch
    insert_deid_report_into_elastic(dicom)

    # Save image thumbnail to disk
    thumbnail_filepath = save_thumbnail_of_dicom(dicom)
    if not thumbnail_filepath:
      log.error('Couldn\'t save thumbnail. Skipping image.')
      continue

    # Save de-identified DICOM to disk
    save_dicom_to_disk(dicom)

    # Insert de-identified DICOM into ElasticSearch
    insert_dicom_into_elastic(dicom)

    if args.wait:
      input("Press Enter to continue...")

  # Print Summary
  elapsed_time = time.time() - t0
  ingest_rate = len(dicom_paths) / elapsed_time
  log.info('{} documents processed '.format(len(dicom_paths)) + 'in {:.2f} seconds at '.format(elapsed_time) + 'rate (documents/s): {:.2f}'.format(ingest_rate))
  log.info('Finished.')
