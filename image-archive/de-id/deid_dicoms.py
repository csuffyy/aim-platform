#!/usr/bin/env python3
#
# File Description:
# Looks up documents in ElasticSearch, finds the DICOM files, processes them, and saves a copy.
#
# Usage:
# source ../environments/local/env.sh
# pkill -9 eog; pkill display; python3 deid_dicoms.py --output_folder ~/aim-platform/image-archive/reactive-search/static/ --output_folder_suffix DEID --input_file ../images/sample/CT-MONO2-16-ort.dcm --fast_crop --input_base_path /home/dan/aim-platform/image-archive/images/ --input_report_base_path /home/dan/aim-platform/image-archive/reports/ # Load DEID dicom
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
from interruptingcow import timeout
from matplotlib import pyplot as plt
from elasticsearch import Elasticsearch
from dateparser.search import search_dates
from dateutil.relativedelta import relativedelta
from skimage.morphology import white_tophat, opening, disk
from deid.dicom import get_files, replace_identifiers, get_identifiers
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True # fixes OSError: broken data stream when reading image file 

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
DATE_FORMAT = '%Y-%m-%d' # standard format YYYY-MM-DD to comply with ElasticSearch searching

def convert_dates_to_standard_format(dicom):
  """Converting dates to standard format YYYY-MM-DD to comply with ElasticSearch searching. It's important that we are confident that we are detecting the correct date because we wouldn't watch to put in place a different date. """
  if args.skip_dates:
    return
  log.info('Converting dates to standard format YYYY-MM-DD.')

  for field in iter_simple_fields(dicom):
    if not 'Date' in field.name:
      continue
    # Skip if not long enough to determine a date with confidence
    if not len(str(field.value))>=8:
      continue
    value = str(field.value).lstrip('0') # remove leading zeros because pydicom has a bug which introduces them. Example: 0095.07.24 given by pydicom is actually found by dcmdump to be 95.07.24
    found_dates = list(datefinder.find_dates(value)) #finds all dates in text using datefinder
    # Skip if more than one date was found since we aren't confident
    if not len(found_dates)==1:
      continue
    found_date = found_dates[0]
    # Skip any date that matches today's date in two sections (YY/MM/DD) because we have problems with datefiner assuming today's date when it can't figure it out
    if count_date_similarity_to_today(found_date) >= 2:
      continue
    # Replace the date with the standard format
    new_value = found_date.strftime(DATE_FORMAT)
    dicom[field.tag] = pydicom.DataElement(field.tag, field.VR, new_value)

def add_derived_fields(dicom):
  log.info('Adding derived fields.')

  # # Calculate PatientAge
  # PatientBirthDate = dicom.get('PatientBirthDate')
  # AcquisitionDate = dicom.get('AcquisitionDate')
  # PatientAge = dicom.get('PatientAge')

  # # PatientAgeInt (Method 1: str to int)
  # try:
  #   if PatientAge is not None:
  #     age = PatientAge # usually looks like '06Y'
  #     if 'Y' in PatientAge:
  #       age = PatientAge.split('Y')
  #       age = int(age[0])
  #     dicom.PatientAge = str(age)
  # except:
  #   log.warning('Falling back for PatientAge')
  # # PatientAgeInt (Method 2: diff between birth and acquisition dates)
  # # Note: Method 2 is higher precision (not just year) and will override method one
  # try:
  #   if PatientBirthDate is not None and AcquisitionDate is not None:
  #     PatientBirthDate = datetime.datetime.strptime(PatientBirthDate, '%Y%m%d')
  #     AcquisitionDate = datetime.datetime.strptime(AcquisitionDate, '%Y%m%d')
  #   age = AcquisitionDate - PatientBirthDate
  #   age = round(age.days / 365,2) # age in years with two decimal place precision
  #   dicom.PatientAge = str(age)
  #   log.debug('Calculated PatientAge to be: %s' % age)
  # except Exception as e:
  #   log.warning('Couldn\'t calculate PatientAgeInt')

  # # Add fake data for local testing only! TODO: Commented out because this is dangerous and has caused me confusion
  if ENVIRON=='local':
    if 'PatientAge' not in dicom:
      log.warning('Adding fake PatientAge')
      dicom.PatientAge = str(random.randint(1,18))
    if 'PatientSex' not in dicom:
      log.warning('Adding fake PatientSex')
      dicom.PatientSex = 'Male' if random.randint(0,1) else 'Female'

def add_patient_age_units(dicom):
  """ convert PatientAge from a weird string to a number. Parse into PatientAgeInYears, PatientAgeInWeeks, PatientAgeInDays.

  Age String: A string of characters with one of the following formats -- nnnD, nnnW, nnnM, nnnY; where nnn shall contain the number of days for D, weeks for W, months for M, or years for Y. Example: "018M" would represent an age of 18 months."""

  PatientAge = dicom.get('PatientAge')
  if not PatientAge:
    # Fall back to calculating age based of difference between birthdate and acquisition date
    PatientBirthDate = dicom.get('PatientBirthDate')
    AcquisitionDate = dicom.get('AcquisitionDate')
    if not PatientBirthDate and not AcquisitionDate:
      # No way to calculate age so returning
      return
    try:
      PatientBirthDate = datetime.datetime.strptime(PatientBirthDate, DATE_FORMAT)
      AcquisitionDate = datetime.datetime.strptime(AcquisitionDate, DATE_FORMAT)
      age_timedelta = AcquisitionDate - PatientBirthDate
      age_in_seconds = age_timedelta.total_seconds()
    except Exception as e:
      log.error('Couldn\'t calculate PatientAgeInt')
      return

  # PatientAge example looks like '06Y'. Character Repertoire: "0"-"9", "D", "W", "M", "Y"
  try:
    if 'Y' in PatientAge:
      age = PatientAge.split('Y')
      age_in_seconds = int(age[0])*31557600 # seconds in a year
    elif 'M' in PatientAge:
      age = PatientAge.split('M')
      age_in_seconds = int(age[0])*2629746 # seconds in a month
    elif 'W' in PatientAge:
      age = PatientAge.split('W')
      age_in_seconds = int(age[0])*604800 # seconds in a week
    elif 'D' in PatientAge:
      age = PatientAge.split('D')
      age_in_seconds = int(age[0])*86400 # seconds in a day
    elif 'S' in PatientAge:
      age = PatientAge.split('S')
      age_in_seconds = int(age[0]) # already in seconds (futureproofing)
    else:
      # Assume PatientAge is in years
      age_in_seconds = float(PatientAge)*31557600 # seconds in a year
  except:
    log.error('Couldn\'t calculate PatientAge')
    return

  PatientAgeInYears = round(age_in_seconds / 31557600.0, 2)
  PatientAgeInMonths = round(age_in_seconds / 2629746.0, 2)
  PatientAgeInWeeks = round(age_in_seconds / 604800.0, 2)
  PatientAgeInDays = round(age_in_seconds / 86400.0, 2)
  PatientAgeInSeconds = age_in_seconds

  # age = round(PatientAgeInDays / 365,2) # age in years with two decimal place precision

  dicom.PatientAge = str(PatientAgeInYears)
  put_to_dicom_private_header(dicom, key='PatientAgeInYears', value=PatientAgeInYears, superkey='Image  ')
  put_to_dicom_private_header(dicom, key='PatientAgeInMonths', value=PatientAgeInMonths, superkey='Image  ')
  put_to_dicom_private_header(dicom, key='PatientAgeInWeeks', value=PatientAgeInWeeks, superkey='Image  ')
  put_to_dicom_private_header(dicom, key='PatientAgeInDays', value=PatientAgeInDays, superkey='Image  ')
  put_to_dicom_private_header(dicom, key='PatientAgeInSeconds', value=PatientAgeInSeconds, superkey='Image  ')

def dicom_to_dict_for_elastic(dicom, log=None, environ=None):
  dicom_metadata = {}
  dicom_metadata['PrivateData'] = []
  dicom_metadata['UnknownData'] = []
  # [dicom_metadata.__setitem__(key,str(dicom.get(key))) for key in dicom.dir() if key not in ['PixelData']]

  for field in iter_simple_fields(dicom):
    value = str(field.value)
    if 'Private' in field.name:
      # Handle our special private data elements
      if len(value) > 7 and value[0:7] in ['Image  ', 'Report ']:
        # This is one of our named private data elements
        try:
          superkey, key, value = extract_key_value_from_field(field)
        except:
          log.warning('could not understand private key format')
          continue
        if superkey == 'Image  ':
          # I don't want PatientAgeInMonths to show up as ImagePatientAgeInMonths, therefore this if block is needed, note the lack of superkey use 
          key = to_short_fieldname(key)
          dicom_metadata[key] = value
        elif superkey == 'Report ':
          key = superkey + key # Example: "Report ReportRaw"
          key = key.replace('ReportReport','Report') # Example: "ReportRaw"
          key = to_short_fieldname(key)
          dicom_metadata[key] = value
      # else:
        # NOTE: PrivateData is disabled in the interest of time and due to search performance concerns
        # This is not one of our sepcial private data elements so save it in two places
        # tag_num = str(field.tag).strip('(,)').replace(' ','') # convert (0019, 0030) to 0019,0030
        # dicom_metadata[tag_num] = value # add it by tag number. Example: dict['0019,0030']=value
        # dicom_metadata['PrivateData'].append(value) # add it to a list of private data
    # elif 'Unknown' in field.name:
      # NOTE: UnknownData is disabled in the interest of time and due to search performance concerns
      # This is not one of our sepcial private data elements so save it in two places
      # tag_num = str(field.tag).strip('(,)').replace(' ','') # convert (0019, 0030) to 0019,0030
      # dicom_metadata[tag_num] = value # add it by tag number. Example: dict['0019,0030']=value
      # dicom_metadata['UnknownData'].append(value) # add it to a list of private data
    else:
      # Standard DICOM fields
      key = to_short_fieldname(field.name) # clean up field names
      dicom_metadata[key] = value

  # for key, value in dicom_metadata.items():
  #   #1
  #   if hasattr(dicom_metadata[key], '_list'):
  #     # Fix for error: TypeError("Unable to serialize ['ORIGINAL', 'SECONDARY'] (type: <class 'pydicom.multival.MultiValue'>)")
  #     dicom_metadata[key] = dicom_metadata[key]._list
  #   #2
  #   if hasattr(dicom_metadata[key], 'original_string'):
  #     # Fix for error: TypeError("Unable to serialize '' (type: <class 'pydicom.valuerep.PersonName3'>)")
  #     dicom_metadata[key] = dicom_metadata[key].original_string
  #   #3
  #   if isinstance(dicom_metadata[key], bytes):
  #     # Fix for error: TypeError("Unable to serialize b'FOONAME^BARNAM' (type: <class 'bytes'>)")
  #     try:
  #       dicom_metadata[key] = dicom_metadata[key].decode("utf-8")
  #     except UnicodeDecodeError as e:
  #       pass
  #   #4
  #   if isinstance(dicom_metadata[key], list):
  #     if len(dicom_metadata[key])>0 and type(dicom_metadata[key][0]) is pydicom.dataset.Dataset:
  #       # Fix for error: TypeError("Unable to serialize 'ProcedureCodeSequence' (type: <class 'pydicom.dataset.Dataset'>)")")
  #       dicom_metadata[key] = dicom_metadata[key].__str__()
  #   #5
  #   # Remove bytes datatype from metadata because it can't be serialized for sending to elasticsearch
  #   if type(dicom_metadata[key]) is bytes:
  #     dicom_metadata.pop(key, None) # remove

    log.debug('%s: %s' % (key, value))

  # PatientBirthDatePretty
  try:
    if 'PatientBirthDate' in dicom_metadata:
      PatientBirthDate = datetime.strptime(dicom_metadata['PatientBirthDate'], '%Y%m%d')
      dicom_metadata['PatientBirthDatePretty'] = datetime.strftime(PatientBirthDate,'%Y-%m-%d')
      datetime.strptime(dicom_metadata['PatientBirthDatePretty'], '%Y-%m-%d')  # just check that it works
  except:
    # log.warning('Didn\'t understand value: %s = \'%s\'' % ('PatientBirthDate', dicom_metadata['PatientBirthDate']))
    dicom_metadata.pop('PatientBirthDatePretty', None) # remove bad formatted metadata
  # AcquisitionDatePretty
  try:
    if 'AcquisitionDate' in dicom_metadata:
      AcquisitionDate = datetime.strptime(dicom_metadata['AcquisitionDate'], '%Y%m%d')
      dicom_metadata['AcquisitionDatePretty'] = datetime.strftime(AcquisitionDate,'%Y-%m-%d')
      datetime.strptime(dicom_metadata['AcquisitionDatePretty'], '%Y-%m-%d')  # just check that it works
  except:
    # log.warning('Didn\'t understand value: %s = \'%s\'' % ('AcquisitionDate', dicom_metadata['AcquisitionDate']))
    dicom_metadata.pop('AcquisitionDatePretty', None) # remove bad formatted metadata

  # # Convert any values that can be displayed as a string (things that need to be numbers should follow this)
  # for k, v in dicom_metadata.items():
  #   # convert to string if not already a string and has str method
  #   if not isinstance(v,str) and '__str__' in dir(v):
  #     dicom_metadata[k] = dicom_metadata[key].__str__()

  return dicom_metadata

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
    log.error('Pixel data not found in DICOM: %s' % dicom_path)
    return

  # Image shape
  log.info('Got pixels of shape: %s TransferSyntaxUID: %s' % (str(img.shape), dicom.file_meta.TransferSyntaxUID))
  if len(img.shape) not in [2,3]:
    # TODO: Support 3rd physical dimension, z-slices. Assuming dimenions x,y,[color] from here on.
    log.warning('Skipping image becasue shape is not 2d-grey or rgb: %s' % dicom_path)
    return
  if len(img.shape) == 3 and img.shape[2] != 3:
    log.warning('Skipping image becasue shape is z-stack: %s' % dicom_path)
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

def get_PHI(dates=False, notdates=False):
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

  if dates or notdates:
    PHI_notdates = []
    PHI_dateobjects = []

    # Sort PHI into two lists: Dates and Not Dates
    for element in PHI:
      element_dt_obj = datefinder.find_dates(element)
      element_dt_obj = list(element_dt_obj)
      if element_dt_obj == []:
        PHI_notdates.append(element)
      else:
        PHI_dateobjects.extend(element_dt_obj)

  if dates and notdates:
    return (PHI_dateobjects, PHI_notdates)
  elif dates and not notdates:
    return PHI_dateobjects
  elif not dates and notdates:
    return PHI_notdates
  else:
    return PHI

def ocr(img, ocr_num=None):
  log.info('Starting OCR...')
  tesseract_config = '--oem %d --psm 3' % ocr_num
  detection = pytesseract.image_to_data(img,config=tesseract_config, output_type=pytesseract.Output.DICT)
  detection = pd.DataFrame.from_dict(detection) # convert to dataframe
  detection = detection[[text.strip() != '' for text in detection.text]] # remove empty strings
  detection = detection.reset_index() # make sure index (row id) doesn't skip numbers
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
      PHI_dateobjects = get_PHI(dates=True)
      _match_text = datematcher(PHI_dateobjects, text, fuzzy=True)
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
  filename = os.path.basename(dicom_path)
  choice_str = 'REJECT' if is_mostly_text else 'ACCEPT'
  width = img_orig.shape[1]
  height = int(14*img_orig.shape[1]/120/RESIZE_FACTOR)+4
  left = 0
  top = img_orig.shape[0]-height
  xy = [left, top, left+width, top+height]
  metadata_fontsize = int(14*img_orig.shape[1]/200/RESIZE_FACTOR)
  img_dtype = str(img_orig.dtype)
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
  # img_enhanced = tophat_proprocess(img_bw)
  img_enhanced = img_bw

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

  dicom_metadata = dicom_to_dict_for_elastic(dicom, log=log, environ=ENVIRON)

  dicom_metadata['dicom_filename'] = os.path.basename(output_image_filepath)
  dicom_metadata['dicom_filepath'] = output_image_filepath
  dicom_metadata['dicom_webpath'] = output_image_webpath
  dicom_metadata['thumbnail_filename'] = os.path.basename(output_thumbnail_filepath)
  dicom_metadata['thumbnail_filepath'] = output_thumbnail_filepath
  dicom_metadata['thumbnail_webpath'] = output_thumbnail_webpath
  if 'PatientAge' in dicom:
    try:
      dicom_metadata['PatientAgeInt'] = float(dicom.get('PatientAge'))
    except:
      pass
  dicom_metadata['original_title'] = 'Dicom'
  dicom_metadata['searchallblank'] = '' # needed to search across everything (via searching for empty string)

  res = es.index(body=dicom_metadata, index=INDEX_NAME, doc_type=DOC_TYPE)

  if res['result'] == 'created':
    log.info('Inserted de-identified dicom into ElasticSearch: %s' % res['_id'])
  else:
    log.error('Insert de-identified report into ElasticSearch FAILED.')
    log.error('elasticsearch index result = %s' % res)

def get_report_from_dicom(dicom, return_only_key_values=False):
  metadata = get_private_metadata_as_dict(dicom)
  if not 'Report ' in metadata:
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

  if 'Report_Raw' in report:
    del report['Report_Raw'] # it was deemed that this was both redundant information and causing a key conflict

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

  if result['hits']['total'] > 0 and not args.overwrite_report:
    log.warning("Not inserting deid report into ElasticSearch because it already exists.")
    return

  # Create report data structure
  report['original_title'] = 'Report'
  report['searchallblank'] = '' # needed to search across everything (via searching for empty string)

  # Insert
  res = es.index(body=report, index=DEID_REPORT_INDEX_NAME, doc_type=DEID_REPORT_DOC_TYPE)

  if res['result'] == 'created':
    log.info('Inserted de-identified report into ElasticSearch: %s' % res['_id'])
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
    metadata[superkey][key]['tag'] = tuple([hex(t) for t in tag])

    # Increment to next field in the report section of the dicom header
    tag[1] += 1
    metadata_part = dicom.get(tag)

  return metadata

def count_date_similarity_to_today(input_date):
  """ Output 0 to 3 depending on how many sections (YY/MM/DD) of the give date match todays date. """
  today = datetime.date.today() #get today's date
  return sum([today.year == input_date.year, today.month == input_date.month, today.day == input_date.day])
  
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

  ## NOTE: Commented out dateparser.search_dates because it adds A LOT of time to processing
  # found_dates_dparser = search_dates(str(text), languages=['en']) #finds all dates in text using dateparser
  # if found_dates_dparser:
  #   found_dates_dparser = list(found_dates_dparser)
  #   for dp_date in found_dates_dparser: #add all the dates found from dateparser to the master list of dates in the correct order as a tuple with the datefinder object first and the part of the text that the date was found in
  #     found_dates.append((dp_date[1], dp_date[0]))
  ## NOTE: For a comparison between dateparser vs datefinder see here: https://github.com/aim-sk/aim-platform/wiki/Performance-Comparison-of-DateFinder-and-DateParser


  for found_date in found_dates: #loop over ONLY found dates as any date has to be in both lists ton continue
    found_date = {
        'object' : found_date[0],
        'string' : found_date[1],
      }
    if found_date['object'] in possibly_dates: 
      returning.add(found_date['string'])

    elif fuzzy: #not an exact match so should check if it is a fuzzy match
      found_date_string = found_date['object'].strftime('%Y%m%d')
      for datetime_object in possibly_dates:
        date_string = datetime_object.strftime('%Y%m%d')

        # The >=75 allows for two different digit swaps assuming 8 characters. And the >=5 confirms that the date is long enough to be an actual date not just a short string of random numbers. And the !=today() ignores "found" dates that match todays date because datefinder assumes today's date if there is missing date information
        if fuzz.ratio(date_string, found_date_string) >= 75 and len(found_date['string']) >= 5 and found_date['object'].date() != datetime.datetime.today().date():
          returning.add(found_date['string'])

    #--------------------OLD CODE-----------------------------------

  # for datetime_object in possibly_dates:
  #   for found_date in found_dates:
  #     found_date = {
  #       'object' : found_date[0],
  #       'string' : found_date[1],
  #     }
  #     if datetime_object == found_date['object']: #if the date matches one that was in input text
  #       returning.add(found_date['string']) #append the line of text where the dates matched

  #     elif fuzzy: #not an exact match so should check if it is a fuzzy match
  #       date_string = datetime_object.strftime('%Y%m%d')
  #       found_date_string = found_date['object'].strftime('%Y%m%d')
  #       # The >=75 allows for two different digit swaps assuming 8 characters. And the >=5 confirms that the date is long enough to be an actual date not just a short string of random numbers. And the !=today() ignores "found" dates that match todays date because datefinder assumes today's date if there is missing date information
  #       if fuzz.ratio(date_string, found_date_string) >= 75 and len(found_date['string']) >= 5 and found_date['object'].date() != datetime.datetime.today().date():
  #         returning.add(found_date['string'])

    #--------------------OLD CODE-----------------------------------
    
  return list(returning)

def to_short_fieldname(field_name):
  """ Example: "Patient's Birth Date" to "PatientBirthDate"""
  short_name = field_name.replace("'s",'') # pydicom gives field names with "'s"
  # short_name = short_name.replace(" ",'')
  short_name = re.sub('[\W_]+','',short_name) # pydicom gives field names with spaces and other non-alphanumeric characters while deid.recipe doesn't have spaces and follows the dicom standard
  return short_name

def match_and_replace_PHI(dicom, field_tag, fuzzy=False):
  """ Finds and replaces PHI in inplace in DICOM be it a date or an exact string match with a UUID."""
  field = dicom.get(field_tag)
  if not field:
    return

  # Skip certain tags # TODO: choose more that shouldn't contain PHI
  short_name = to_short_fieldname(field.name)
  if short_name in cleaned_tag_names_list:
    return
  # Skip values less than 3 characters
  if len(str(field.value)) <= 3:
    return

  if (field != None): #check if the field exists
    (PHI_dateobjects, PHI_notdates) = get_PHI(dates=True, notdates=True) #get all PHI values so far
    # PHI_dateobjects.extend(list(datefinder.find_dates("2035/02/15")))
    # PHI_dateobjects.extend(list(datefinder.find_dates("2035/02/16")))
    # PHI_dateobjects.extend(list(datefinder.find_dates("2034/06/20")))
    # PHI_dateobjects.extend(list(datefinder.find_dates("2035/11/02")))
    if not PHI_notdates and not PHI_dateobjects:
      return

    # Update DICOM
    try:
      #replace exact matches with UID
      value = match_and_replace_exact(dicom, field_tag, PHI_notdates)
      if value is not None and str(value) != str(field.value): # only if a replacement was made
        field.value = value
        dicom[field.tag] = pydicom.DataElement(field.tag, field.VR, field.value) # set back into dicom

      #replace possible date matches that aren't directly in text with UID
      value = match_and_replace_dates(dicom, field_tag, PHI_dateobjects, fuzzy)
      if value is not None and str(value) != str(field.value): # only if a replacement was made
        field.value = value
        dicom[field.tag] = pydicom.DataElement(field.tag, field.VR, field.value) # set back into dicom

    except Exception as e:
      print(traceback.format_exc())
      log.error('Failed to set dicom field "%s" with new value. The original value will remain in place without any redaction.' % field)
      raise e

def match_and_replace_exact(dicom, field_tag, PHI):
  """matches and replaces PHI dates that were the exact same format as those found in the specified field
  Returns the updated field of the dicom"""
  field = dicom.get(field_tag)
  value = str(field.value)
  superkey = None

  # Avoid replacing our superkey and key stuff (Part 1)
  if len(value) > 7 and value[0:7] in ['Image  ', 'Report ']:
    (superkey, key, value) =  extract_key_value_from_field(field)

  for a_PHI in PHI:
    if a_PHI.upper() in value.upper():
      if len(a_PHI) >= 3:
        _dict = {field.name: a_PHI, 'new_path': output_image_filepath, 'orig_path': dicom_path}
        start_loc = value.upper().find(a_PHI)
        end_loc = start_loc + len(a_PHI)
        UID = generate_uid(_dict, field_name=field.name)
        value = value[0:start_loc] + str(UID) + value[end_loc:]
    else:
      return

  # Avoid replacing our superkey and key stuff (Part 2)
  if superkey:
    value = "%s%s: %s" % (superkey, key, str(value))

  return value

def match_and_replace_dates(dicom, field_tag, PHI_dateobjects, fuzzy=False):
  """matches and replaces PHI dates that were not the exact same format as those found in the specified field
  Returns the updated field of the dicom"""
  field = dicom.get(field_tag) 
  value = str(field.value)

  # For faster testing, allow skipping slow and frequent datefinding
  if args.skip_dates:
    return

  # To speed up computation don't try to match dates if we can till it's not going to be a date.
  # Skip if not 2 or more numbers
  if not re.match('.*[0-9].*[0-9].*', value.replace('\n','')):
    return
  # Skip if is UUID
  try:
    if isinstance(uuid.UUID(value), uuid.UUID):
      return
  except:
    # if it's not a UUID pass this and check it for a date
    pass

  found_date_strings = datematcher(PHI_dateobjects, value, fuzzy) #get all dates from the specified field of the dicom

  for found_date in found_date_strings: #check where the date is and replace it 
  # Split found date string into parts because sometimes we over detect and include words like "on" so we'll next loop over the parts looking for the just the date to replace
    split_day = re.split('[ :]', found_date)
    for split_piece in split_day:
      # Skip dates less than 5 characters
      if len(split_piece) < 5:
        continue

      date_string_tuple = datefinder.find_dates(split_piece, source= True)
      date_string_tuple = list(date_string_tuple)

      if date_string_tuple != []: #if a date was found
        _dict = {field.name: date_string_tuple[0][0].strftime(DATE_FORMAT), 'new_path': output_image_filepath, 'orig_path': dicom_path}
        UID = generate_uid(_dict, field_name=field.name)
        value = value.replace(date_string_tuple[0][1], str(UID))


  return value

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
    elif "a bytes-like object is required, not \'str\'" in str(e):
      tag = (str(e)[10:14],str(e)[16:20]) # (0019, 109d)
      dicom[tag].VR='LT'
      dicom.save_as(output_image_filepath)
      log.error('Successfully recovered from error and saved de-identified dicom to disk: %s\n' % output_image_filepath)
    else:
      raise e


def save_deid_report_to_disk(dicom):
  """save the edited file to the specified file given in the dicom. Also saves location of de-id'd report into dicom."""
  report = get_report_from_dicom(dicom)

  if not report:
    log.warning('No report associated with DICOM, so not saving deid report to disk')
    return

  if not os.path.exists(output_report_filepath) or args.overwrite_report:
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
  """ Add new private data in dicom metadata. Overwritting can be done if you just provide a tag """
  if not key:
    raise Exception('put_to_dicom_private_header() requires a key')
  if superkey not in ['Report ', 'Image  ']:
    raise Exception('Currently only supporting superkeys "Report " or "Image  ".')

  dicom_datatype = 'LT' # Dicom datatype Value Representation

  if tag:
    # This can overwrite an existing piece of data (this is a needed feature)
    loc = tag
    # if tag in dicom: # Turns out this is not so unexpected because we overwrite when we're replacing report fields with de-id report fields.
    #   log.warning('Unexpected overwriting of data in dicom private header. Field was: %s'% dicom[tag])
  elif key:
    # Remove all non-word characters (everything except numbers and letters)
    key = re.sub(r"[^\w\s]", '', key)
    key = re.sub(r"\s+", '', key)

    # Loop until the key is found in header or a free location for metadata is found in header
    loc_group = 0x0019
    loc_element = 0x0030
    loc = (loc_group, loc_element)
    while loc in dicom:
      # Check if we found key
      field = dicom[loc]
      a_superkey, a_key, a_value = extract_key_value_from_field(field)
      if key == a_key and superkey == a_superkey:
        break
      # Increment to use higher index on next loop
      loc_element = loc_element + 1 
      loc = (loc_group, loc_element)

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
    key = to_short_fieldname(key)
    put_to_dicom_private_header(dicom, key=key, value=value, superkey='Report ')
  put_to_dicom_private_header(dicom, key='webpath', value=output_report_webpath, superkey='Report ')

def already_cleaned_tag_names():
  with open(args.deid_recipe, 'r') as f:
    names = f.read().split('\n')
    names = [line.split()[1] for line in names if 'REPLACE' in line] # convert "REPLACE AdmissionID func:generate_uid" to "AdmissionID"
    return names

def dont_replace_field_names():
  with open(args.deid_recipe, 'r') as f:
    names = f.read().split('\n')
    names = [line.split()[2] for line in names if 'KEEP' in line] # convert "# KEEP AdmissionID" to "AdmissionID"
    return names

def get_report_deid_recipe():
  """ Instructions for how to deidentify report.

  Example return:
  [{'operation': 'REPORT_REPLACE', 'search_text': 'BirthDate'},
 {'operation': 'REPORT_REPLACE', 'search_text': 'MedicalRecordNumber'},
 {'operation': 'REPORT_REPLACE_AFTER',
  'parameter': 'until_newline',
  'search_text': 'ELECTRONICALLY APPROVED and SIGNED on'},
 {'operation': 'REPORT_REPLACE_AFTER',
  'parameter': '10',
  'search_text': 'Transcriptionist'}]

  @return replace_keys is a list of keys in the recipe for REPORT_REPLACE lines
  @return report_replace_after is a list of keys in the recipe for REPORT_REPLACE_AFTER lines
  """

  ret = []
  with open(args.deid_recipe, 'r') as f:
    lines = f.read().split('\n')
    # Parse REPORT_REPLACE lines
    replace_keys = [line.split()[2] for line in lines if 'REPORT_REPLACE ' in line] # convert "# REPORT_REPLACE OrderNumber" to "OrderNumber"
    for replace_key in replace_keys:
      ret.append({'operation': 'REPORT_REPLACE', 'search_text': replace_key})

    # Parse REPORT_REPLACE_AFTER lines
    # convert '# REPORT_REPLACE_AFTER "Transcriptionist" 10' to tuple('Transcriptionist', '10')
    replace_after_keys = [line for line in lines if 'REPORT_REPLACE_AFTER' in line]
    for line in replace_after_keys:
      start_loc = line.find('REPORT_REPLACE_AFTER') + len('REPORT_REPLACE_AFTER') # get text after the special command identifier
      line_parts = line[start_loc:].split() # split up the text by spaces (as per the syntax)
      last_line_part = len(line_parts) - 1 # the last line part is the parameter
      parameter = line_parts[last_line_part]
      search_text = ' '.join(line_parts[0:last_line_part]) # search string is the unique text identifier (key) used to signify a PHI section of the report
      search_text = search_text[1:len(search_text)-1] # remove leading and trailing quote
      ret.append({'operation': 'REPORT_REPLACE_AFTER', 'search_text': search_text, 'parameter': parameter})

    return ret, replace_keys

def deidentify_report(dicom):
  # Iterate over keys to replace with UUIDs. Store PHI values
  # Apply algorithm to "Raw": (1) find and replace stored PHI values and (2) and apply the special replace rules to raw only
  if not report:
    return

  # Get report from DICOM (which has info about tag numbers)
  dicom_report = get_report_from_dicom(dicom)

  if not dicom_report:
    return

  # Get rules for deidentification
  (recipe, replace_keys) = get_report_deid_recipe()

  # Replace PHI in report
  found_report_PHI = {} # found PHI and their values
  found_report_PHI_UID = {} # found PHI and their UUIDs
  global found_PHI_count_header
  for key, data in dicom_report.items():
    tag = data['tag']
    value = data['value']
    # Only replace if it's a key in our report recipe or (in the standard REPLACE recipe section but not if it already has had a UUID replaced, we don't want to replace a UUID with a UUID)
    if key in replace_keys or (key in cleaned_tag_names_list and not count_uuids(value)):
      # Generate replacement value
      _dict = {key: value, 'new_path': output_image_filepath, 'orig_path': dicom_path}
      UID = generate_uid(_dict, field_name=key)
      # Replace value in DICOM
      put_to_dicom_private_header(dicom, key=key, tag=tag, value=UID, superkey='Report ')
      found_report_PHI[key] = value # store this PHI
      found_report_PHI_UID[key] = UID # store this UUID
      found_PHI_count_header += 1 # count this PHI

  # Replace the found PHI in the raw report with UUIDs. The raw report should be the only duplicated report data that needs this special treatment
  raw_report = dicom_report['Raw']['value']
  tag = dicom_report['Raw']['tag']
  for key, value in found_report_PHI.items():
    UID = found_report_PHI_UID[key]
    raw_report = raw_report.replace(value, UID)

  # Handle REPORT_REPLACE_AFTER which should remove charaters after the found string
  for rule in recipe:
    if rule['operation'] == 'REPORT_REPLACE_AFTER':
      # Get start stop indexes of text to remove
      start_loc = raw_report.find(rule['search_text']) + len(rule['search_text']) # start right after the search_text
      if rule['parameter'] == 'until_newline':
        end_loc = raw_report.find('\n', start_loc) # stop at the next new line
      else:
        distance = int(rule['parameter'])
        end_loc = start_loc + distance # stop after this many characters
      # Remove the PHI
      value = raw_report[start_loc:end_loc]
      _dict = {key: value, 'new_path': output_image_filepath, 'orig_path': dicom_path}
      UID = generate_uid(_dict, field_name=key)
      raw_report = raw_report[0:start_loc] + ' ' + str(UID) + ' ' + raw_report[end_loc:len(raw_report)]
  # Store
  put_to_dicom_private_header(dicom, key='Raw', tag=tag, value=raw_report, superkey='Report ')

def count_uuids(text):
  """ Returns number of lines that contain UUID. Counts max 1 uuid per line """
  return len(re.findall('.*[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12}.*', text))

def iter_simple_fields(dicom):
  for field in dicom.iterall():
    if field is int:
      continue
    if field is None:
      continue
    # Skip pixel data
    if field.name == 'Pixel Data':
      continue
    if field.value.__class__ in [pydicom.sequence.Sequence]:
      continue
    # Note: commented out because not needed?
    # # Skip objects of this kind because they can't be made into strings, perhaps go deeper. Update: not true?
    # if field.value.__class__ in [pydicom.valuerep.PersonName3, pydicom.multival.MultiValue, pydicom.valuerep.DSfloat, pydicom.valuerep.IS, int, pydicom.sequence.Sequence]:
    #
    # Note: commented because can't going deeper into dicom isn't working
    # if field.VR == 'SQ' or (hasattr(field, 'get') and len(field.get('tags'))):
    #   for f in field:
    #     yield f
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

  cleaned_header_dicom = cleaned_files[0] # we only pass in one at a time
  # note: cleaned_header_dicom is not a full dicom. It is not as functional as the "dicom" variable
  if args.log_PHI:
    log.info(found_PHI)

  # Copy from "cleaned_header_dicom" to "dicom" variable so that UUIDs take place of PHI. "dicom" is the preferred variable
  for field_name in found_PHI.keys():
    dicom.data_element(field_name).value = cleaned_header_dicom.data_element(field_name).value
    
  # Look for detected PHI in all DICOM fields and replace with UUIDs (this will de-id the report if present in the DICOM)
  dont_replace_field_names_list = dont_replace_field_names()
  for field in iter_simple_fields(dicom):
    if to_short_fieldname(field.name) in dont_replace_field_names_list:
      continue # skip fields we've explicity said we want to keep in our deid recipe
    match_and_replace_PHI(dicom, field.tag)

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
  parser.add_argument('--log_PHI', action='store_true', help='Log PHI for debugging purposes only')
  parser.add_argument('--overwrite_report', action='store_true', help='Overwrite existing report on disk and in elasticsearch')
  parser.add_argument('--skip_dates', action='store_true', help='For faster testing, allow skipping slow and frequent datefinding')
  parser.add_argument('--timeout', type=int, default=1000, help='Limit the amonut of time processing one image')

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
  log.info("Settings: %s=%s" % ('log_PHI', not args.log_PHI))
  log.info("Settings: %s=%s" % ('overwrite_report', not args.overwrite_report))
  log.info("Settings: %s=%s" % ('skip_dates', not args.skip_dates))
  log.info("Settings: %s=%s" % ('timeout', not args.timeout))
  

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

  args.output_folder = os.path.abspath(os.path.expanduser(os.path.expandvars(args.output_folder))) # /home/dan/aim-platform/image-archive/reactive-search/static/
  if args.output_folder_suffix:
    log.info('args.output_folder_suffix = %s' % args.output_folder_suffix)
    args.output_folder = os.path.join(args.output_folder, args.output_folder_suffix) # /home/dan/aim-platform/image-archive/reactive-search/static/deid/

  # MAIN LOOP: Process each dicom
  for idx, dicom_path in enumerate(dicom_paths):
    try:
      with timeout(args.timeout, exception=RuntimeError): # Timeout if too slow
        log.info('\n\nProcessing DICOM path: %s' % dicom_path)
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
        args.input_base_path = os.path.abspath(os.path.expanduser(os.path.expandvars(args.input_base_path))) # /home/dan/Favourite_Images/
        if args.input_base_path not in dicom_path:
          raise Exception('Error: Couldnt find "args.input_base_path" in "dicom_path". Please check your CLI arguments.')
        dicom_path_short = dicom_path.replace(args.input_base_path,'').lstrip('/') # MRI/1795084_117225373.dcm
        log.info('dicom_path = %s' % dicom_path)
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
          input_report_filepath = os.path.abspath(os.path.expanduser(os.path.expandvars(report['filepath']))) # example: /home/dan/aim-platform/image-archive/reports/sample/Report_55123.txt
          if args.input_report_base_path not in input_report_filepath:
            raise Exception('Error: Couldnt find "args.input_report_base_path" in "input_report_filepath". Please check your CLI arguments.')
          report_path_short = input_report_filepath.replace(args.input_report_base_path,'').lstrip('/') # example: sample/Report_55123.txt
          output_report_filepath = os.path.join(args.output_folder, 'report', report_path_short) # example: /home/dan/aim-platform/image-archive/reactive-search/static/deid/report/sample/Report_55123.txt
          output_report_webpath = os.path.join('report', report_path_short) # example: report/sample/Report_55123.txt
          if args.output_folder_suffix:
            output_report_webpath = os.path.join(args.output_folder_suffix, output_report_webpath) # example: deid/report/sample/Report_testing.txt
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

        # Convert dates to standard format YYYY-MM-DD to comply with ElasticSearch searching and DWV viewing.
        convert_dates_to_standard_format(dicom)

        # Add derived fields (must happen before de-identification since that could remove needed data)
        add_derived_fields(dicom)
        
        # Convert PatientAge into PatientAgeInYears, PatientAgeInWeeks, PatientAgeInDays, etc.
        add_patient_age_units(dicom)

        # Add report
        add_report(dicom, report)
        
        # Add UUID
        uid = add_uuid(dicom)

        # Record where the original DICOM file came from before it was de-identified
        put_to_dicom_private_header(dicom, key='filepath_orig', value=dicom_path, superkey='Image  ')
        put_to_dicom_private_header(dicom, key='filepath', value=output_image_filepath, superkey='Image  ')
        put_to_dicom_private_header(dicom, key='webpath', value=output_image_webpath, superkey='Image  ')
        put_to_dicom_private_header(dicom, key='thubnail_webpath', value=output_thumbnail_webpath, superkey='Image  ')
        
        # Record what code touched the image
        add_audit_to_dicom(dicom)

        if not args.no_deidentify:
          log.info('###################')
          log.info('##  De-Identify  ##')
          log.info('###################')

          # Store cleaned tag names so that they can be skipped at later times for faster performance
          cleaned_tag_names_list = already_cleaned_tag_names()

          # De-Identify Metadata (including much of the report) (and keep track of value replacements ie. linking) (and this will populate the found_PHI global variable and so must come before other de-identification)
          deidentify_header(dicom)

          # De-Identify Report
          deidentify_report(dicom)

          # Record how many PHI was found and replaced in ElasticSearch
          store_number_of_redacted_PHI(uid)

          # Process pixels (de-id pixels and save debug gif)
          result = process_pixels(dicom)
          if result is None:
            log.warning('Couldnt read pixels so skipping: %s' % dicom_path)
            continue

          log.info('Found %s fields matching PHI died.recipe.' % len(found_PHI.keys()))
          log.info('Found %s unique pieces of PHI.' % len(set(found_PHI.values())))
          log.info('Redacted %s instances of PHI from header and report' % found_PHI_count_header)
          log.info('Redacted %d instances of PHI from pixels' % found_PHI_count_pixels)

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

    except RuntimeError as e:
      print(traceback.format_exc())
      log.error("didn't finish within %s seconds going to next image" % args.timeout)
      continue


  # Print Summary
  elapsed_time = time.time() - t0
  ingest_rate = len(dicom_paths) / elapsed_time
  log.info('{} documents processed '.format(len(dicom_paths)) + 'in {:.2f} seconds at '.format(elapsed_time) + 'rate (documents/s): {:.2f}'.format(ingest_rate))
  log.info('Finished.')

