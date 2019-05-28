#!/usr/bin/env python3
#
# File Description:
# Looks up documents in ElasticSearch, finds the DICOM files, processes them, and saves a copy.
#
# Usage:
# source ../environments/local/env.sh
# python3.7 deid_dicoms.py --input_range 1-10 --output_folder ./tmp/
# OR
# python3.7 deid_dicoms.py --input_files file_list.txt --output_folder ./tmp/
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
import time
import uuid
import pickle
import pydicom
import logging
import datetime
import argparse
import matplotlib
import pytesseract
import collections
import numpy as np
import pandas as pd
import elasticsearch

from IPython import embed
# embed() # drop into an IPython session
from random import randint
from itertools import chain
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from elasticsearch import helpers
from deid.config import DeidRecipe
from matplotlib import pyplot as plt
from elasticsearch import Elasticsearch
from dateutil.relativedelta import relativedelta
from skimage.morphology import white_tophat, disk
from deid.dicom import get_files, replace_identifiers, get_identifiers
from PIL import Image, ImageDraw, ImageFont, ImageFilter

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
RESIZE_FACTOR = 4 # how much to blow up image to make OCR work better
MATCH_CONF_THRESH = 50
OUTPUT = 'gifs'
OUTPUT = 'screen'
log.info("Settings: %s=%s" % ('ELASTIC_IP', ELASTIC_IP))
log.info("Settings: %s=%s" % ('ELASTIC_PORT', ELASTIC_PORT))
log.info("Settings: %s=%s" % ('INDEX_NAME', INDEX_NAME))
log.info("Settings: %s=%s" % ('DOC_TYPE', DOC_TYPE))
log.info("Settings: %s=%s" % ('LINKING_INDEX_NAME', LINKING_INDEX_NAME))
log.info("Settings: %s=%s" % ('LINKING_DOC_TYPE', LINKING_DOC_TYPE))
log.info("Settings: %s=%s" % ('RESIZE_FACTOR', RESIZE_FACTOR))
log.info("Settings: %s=%s" % ('MATCH_CONF_THRESH', MATCH_CONF_THRESH))
log.info("Settings: %s=%s" % ('OUTPUT', OUTPUT))

if OUTPUT == 'screen':
  matplotlib.use('TkAgg')
elif OUTPUT in ['gifs']:
  matplotlib.use('Agg')


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
  except:
    log.warning('Couldn\'t calculate PatientAge')
    log.warning('Problem image was: %s' % filepath)

  return dicom

def get_pixels(input_filepath):
  log.info('Getting pixels for in DICOM: %s' % input_filepath)
  dicom = pydicom.dcmread(input_filepath, force=True)

  # Guess a transfer syntax if none is available
  if 'TransferSyntaxUID' not in dicom.file_meta:
    dicom.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian  # 1.2.840.10008.1.2
    dicom.add_new(0x19100e, 'FD', [0,1,0]) # I have no idea what this last vector should actually be
    dicom[0x19100e].value = 'Assumed TransferSyntaxUID'
    log.warning('Assumed TransferSyntaxUID')
    log.warning('Problem image was: %s\n' % filepath)

  # Get Pixels
  if not 'pixel_array' in dicom:
    img = dicom.pixel_array
  else:
    log.error('Pixel data not found in DICOM: %s' % filename)
    return

  # Image shape
  if img.shape == 0:
    log.warning('Image size is 0: %s' % filename)
    # copyfile(filepath, '%s_%s' % (output_path, filename))
    return
  if len(img.shape) not in [2,3]:
    # TODO: Support 3rd physical dimension, z-slices. Assuming dimenions x,y,[color] from here on.
    log.warning('Image shape is not 2d-grey or rgb: %s' % filename)
    # copyfile(filepath, '%s_%s' % (output_path, filename))
    return

  # Colorspace
  if 'PhotometricInterpretation' in dicom and 'YBR' in dicom.PhotometricInterpretation:
    # Convert from YBR to RGB
    # TODO: Is there a more efficient way?
    image = Image.fromarray(img,'YCbCr')
    image = image.convert('RGB')
    img = np.array(image)
    # plt.imshow(img, cmap='gray')
    # plt.show()
    # More image modes: https://pillow.readthedocs.io/en/3.1.x/handbook/concepts.html#concept-modes
  
  img_orig = img

  # Convert to greyscale
  if len(img.shape) == 3:
    image = Image.fromarray(img,'RGB')
    image = image.convert('L')
    img = np.array(image)

  # Upscale image to improve OCR
  img = cv2.resize(img, dsize=(img.shape[1]*RESIZE_FACTOR, img.shape[0]*RESIZE_FACTOR), interpolation=cv2.INTER_CUBIC)
  img_orig = cv2.resize(img_orig, dsize=(img_orig.shape[1]*RESIZE_FACTOR, img_orig.shape[0]*RESIZE_FACTOR), interpolation=cv2.INTER_CUBIC)

  return (img, img_orig, dicom) # return greyscale image and original rgb image

def flatten(l):
  for el in l:
    if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
      yield from flatten(el)
    else:
      yield el

def tophat_proprocess(img):
  # TopHat to strengthen text
  selem = disk(10)
  img = white_tophat(img, selem)
  return img

def blur_sharpen_preprocess(img):
  image = Image.fromarray(img,'L')
  # Blur
  image = image.filter( ImageFilter.GaussianBlur(radius=1.5))
  # Sharpen Edges a Lot
  image = image.filter( ImageFilter.EDGE_ENHANCE_MORE )
  img = np.array(image)
  return img

def get_PHI(dicom):
  PHI = []
  # Build list of PHI to look for: MNR, FirstName, LastName
  PatientName = dicom.get('PatientName')
  PatientID = dicom.get('PatientID')
  if PatientName:
    name_parts = re.split('\^| ',str(dicom.PatientName)) # PatientName is typically: FirstName^LastName
    PHI = [PHI, name_parts]
  if PatientID:
    PHI = [PHI, PatientID]
  PHI = list(flatten(PHI))
  PHI = [x.upper() for x in PHI if x is not None] # ensure upper case
  return PHI

def ocr(img, ocr_num=None):
  log.info('Starting OCR...')
  # Do OCR
  tesseract_config = '--oem %d --psm 3' % ocr_num
  detection = pytesseract.image_to_data(img,config=tesseract_config, output_type=pytesseract.Output.DICT)
  detection = pd.DataFrame.from_dict(detection) # convert to dataframe
  detection = detection[detection.text != ''] # remove empty strings

  if detection.empty:
    log.warning('No text found by OCR')

  return detection

def match(search_strings, detection, ocr_num=None):
  if detection.empty or search_strings is None or search_strings == []:
    return

  match_confs = [] # confidence
  match_texts = [] # closest match
  match_bool = [] # whether it's a positive match
  for i in range(0,len(detection)):
    text = detection.text.iloc[i]
    valid = True
    if len(text) <= 1: # check that text is longer than one character
      valid = False
    elif re.match('.*\w.*', text) is None: # check that text contains letter or number
      valid = False

    if valid:
      match_text, match_conf = process.extractOne(text, search_strings, scorer=fuzz.ratio)
      match_texts.append(match_text)
      match_confs.append(match_conf)
      if match_conf > MATCH_CONF_THRESH:
        match_bool.append(True)
      else:
        match_bool.append(False)
    else:
      match_texts.append('')
      match_confs.append(0)
      match_bool.append(False)

  detection['match_text'] = match_texts
  detection['match_conf'] = match_confs
  detection['match_bool'] = match_bool

  return detection

def clean_pixels(dicom, img_orig, detection, output_filepath, input_filepath):
  """ Put black boxes in image to "clean" it """
  removals = []
  yellow = 'rgb(255, 255, 0)' # yellow color
  black = 'rgb(0, 0, 0)' # yellow input_color
  dicom_pixels = dicom.pixel_array

  image_orig = Image.fromarray(img_orig)
  image_color = Image.fromarray(img_orig)
  draw_color = ImageDraw.Draw(image_color)

  # Draw Annotations
  for index, row in detection.iterrows():
    if row.match_bool:
      top = row.top
      left = row.left
      height = row.height
      width = row.width
      ocr_text = row.text
      ocr_conf = row.conf
      match_conf = row.match_conf
      match_text = row.match_text

      # Black out in actual dicom pixels
      sml_left = int(left / RESIZE_FACTOR)
      sml_top = int(top / RESIZE_FACTOR)
      sml_width = int(width / RESIZE_FACTOR)
      sml_height = int(height / RESIZE_FACTOR)
      dicom_pixels[sml_top:sml_top+sml_height, sml_left:sml_left+sml_width] = 0
      dicom_pixels[sml_top, sml_left:sml_left+sml_width] = np.max(dicom_pixels)
      dicom_pixels[sml_top+sml_height, sml_left:sml_left+sml_width] = np.max(dicom_pixels)
      dicom_pixels[sml_top:sml_top+sml_height, sml_left] = np.max(dicom_pixels)
      dicom_pixels[sml_top:sml_top+sml_height, sml_left+sml_width] = np.max(dicom_pixels)

      # Black out pixels with debug info overlayed in boxes (for debugging only)
      annotation = 'ocr: %s, %d\nmatch: %s, %d' % (ocr_text, ocr_conf, match_text, match_conf)
      xy = [left, top, left+width, top+height]
      font = ImageFont.truetype('Roboto-Regular.ttf', size=int(height/2.5))
      draw_color.rectangle(xy, fill=black, outline=yellow)
      draw_color.multiline_text((left, top), annotation, fill=yellow, font=font)

      # Store removal details
      removals.append({
        'top': top,
        'left': left,
        'height': height,
        'width': width,
        'ocr_text': ocr_text,
        'ocr_conf': ocr_conf,
        'match_conf': match_conf,
        'match_text': match_text,
      })

  if len(removals)==0:
    log.warning('No detected text closely matches the PHI: %s' % input_filepath)

  # Display
  if OUTPUT == 'screen':
    image_color.show()
  elif OUTPUT == 'gifs':
    image_orig = image_orig.convert('RGB')
    image_color = image_color.convert('RGB')
    frames = [image_color, image_orig]
    frames[0].save('%s.gif' % output_filepath, format='GIF', append_images=frames[1:], save_all=True, duration=1000, loop=0)
    log.info('Saved GIF: %s.gif' % output_filepath)

  # Store updated pixels in DICOM
  if dicom.file_meta.TransferSyntaxUID.is_compressed:
    dicom.decompress()
  dicom.PixelData = dicom_pixels.tobytes()

  return (dicom, removals)

def process_pixels(input_filepath, output_filepath):
  # Get Pixels
  img_bw, img_orig, dicom = get_pixels(input_filepath)

  if img_bw is None:
    return

  # Get PHI
  PHI = get_PHI(dicom)

  # Preprocess Pixels (Variety #1)
  log.info('Processing 1...')
  img_enhanced = tophat_proprocess(img_bw)

  # Detect Text with OCR
  detection = ocr(img_enhanced, ocr_num=2)

  # Detect if image has so much text that it's probably a requisition and should be rejected or so little text that it should be accepted without PHI matching


  # Match Detected Text to PHI
  log.info('Matching 1...')
  detection = match(PHI, detection, ocr_num=2)

  # Preprocess Pixels (Variety #2)
  log.info('Processing 2...')
  img_enhanced = blur_sharpen_preprocess(img_bw)

  # Detect Text with OCR
  detection2 = ocr(img_enhanced, ocr_num=2)

  # Match Detected Text to PHI
  log.info('Matching 2...')
  detection2 = match(PHI, detection2, ocr_num=2)

  if detection is None and detection2 is None:
    log.warn('Cleaned 0 PHI areas in pixels.')
    return dicom
  
  # Combine detection results of different preprocessing
  detection = pd.concat([detection, detection2], ignore_index=True, sort=True)

  # Clean Image Pixels
  dicom, removals = clean_pixels(dicom, img_orig, detection, output_filepath, input_filepath)
  log.info('Cleaned %s PHI areas in pixels.' % len(removals))

  return dicom

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
  """ This function generates a uuid to put in place of PHI and trackes the linking between UUID and PHI by inserting into ElasticSearch """
  orig = dicom_dict[field_name] if field_name in dicom_dict else ''
  uid = str(uuid.uuid4()) # otherwise generate new id

  # Look to find existing linking in ElasticSearch
  if save_to_elastic:
    res = lookup_linking(orig)

    if len(res):
      # use id found in elastic
      uid = res[0]['_source']['new']
    else:
      # otherwise insert a new linking
      query = {'orig': orig, 'new': uid, 'field': field_name, 'date': datetime.datetime.now(), 'orig_path': dicom_dict['orig_path'], 'new_path': dicom_dict['new_path']}
      if '_id' in dicom_dict:
        query['id'] = dicom_dict['_id'] # Use same elasticsearch document ID from input index in the new index
      res = es.index(body=query, index=LINKING_INDEX_NAME, doc_type=LINKING_DOC_TYPE)

    log.debug('Linking %s:%s-->%s' % (field_name, orig, uid))

  return uid

def get_report_as_dict(cleaned_pixels_dicom):
  report_dict = {}
  hex_list = [0x0019, 0x0030]
  report_part = cleaned_pixels_dicom.get(hex_list)
  while(report_part is not None):
    seperate_key_value = report_part.value.split(": ")
    report_dict[seperate_key_value[0].strip('report ')] = ":".join(seperate_key_value[1:])

    #icrements the hexidecimal values and replaces the hex string
    hex_list[1] += 1
    #gets the next values for the next possible key and value in the dictionary
    report_part = cleaned_pixels_dicom.get(hex_list)

  return report_dict


if __name__ == '__main__':
  # Set up command line arguments
  parser = argparse.ArgumentParser(description='Looks up documents in ElasticSearch, finds the DICOM files, processes them, and saves a copy.')
  parser.add_argument('--input_range', help='Positional document numbers in ElasticSearch (ex. 1-10). These documents will be processed.')
  parser.add_argument('--input_files', help='List of DICOM files which will be processed.')
  parser.add_argument('--no_elastic', action='store_true', help='Skip saving metadata to ElasticSearch.')
  parser.add_argument('--no_pixels', action='store_true', help='Skip de-identification of pixels.')
  parser.add_argument('--deid_recipe', default='deid.dicom', help='De-id rules.')
  parser.add_argument('--output_folder', help='Save processed DICOM files to this path.')
  parser.add_argument('--input_dicom_filename', help='Process only this DICOM by name (looked up in ElasticSearch)')
  args = parser.parse_args()
  output_folder = args.output_folder
  save_to_elastic = not args.no_elastic
  no_pixels = args.no_pixels
  input_dicom_filename = args.input_dicom_filename
  input_range = args.input_range
  input_files = args.input_files
  deid_recipe = args.deid_recipe
  log.info("Settings: %s=%s" % ('output_folder', output_folder))
  log.info("Settings: %s=%s" % ('save_to_elastic', save_to_elastic))
  log.info("Settings: %s=%s" % ('no_pixels', no_pixels))
  log.info("Settings: %s=%s" % ('input_dicom_filename', input_dicom_filename))
  log.info("Settings: %s=%s" % ('input_range', input_range))
  log.info("Settings: %s=%s" % ('input_files', input_files))
  log.info("Settings: %s=%s" % ('deid_recipe', deid_recipe))

  recipe = DeidRecipe(deid_recipe) # de-id rules

  if save_to_elastic:
    es = Elasticsearch([{'host': ELASTIC_IP, 'port': ELASTIC_PORT}])

  # Get List of Dicoms from a file
  if input_files:
    fp = open(input_files) # Open file on read mode
    dicom_paths = fp.read().split("\n") # Create a list containing all lines
    fp.close() # Close file
    dicom_paths = list(filter(None, dicom_paths)) # remove empty lines
    doc_ids = None
  # Lookup one input file from Elastic
  elif input_dicom_filename:
    query = {
      "_source": ["_id", "dicom_filepath"],
      "query": {
        "term": {
          "dicom_filename.keyword": input_dicom_filename
        }
      }
    }
  # Lookup many input files from Elastic
  elif input_range:
    input_start, input_end = [int(i) for i in input_range.split('-')]
    query = {
      "_source": ["_id", "dicom_filepath"],
      "from": input_start,
      "size": input_end
    }
  # Actually get documents from ElasticSearch
  if input_dicom_filename or input_range:
    results = es.search(body=query, index=INDEX_NAME)
    log.info("Number of Search Hits: %d" % len(results['hits']['hits']))
    results = results['hits']['hits']
    dicom_paths = [res['_source']['dicom_filepath'] for res in results]
    doc_ids = [res['_id'] for res in results]

  log.info("Number of input files: %d" % len(dicom_paths))

  # Prepare documents for de-identification
  dicom_dicts = get_identifiers(dicom_paths)
  # TODO: DON"T USE LOOP HERE
  for idx, path in enumerate(dicom_dicts):
    filename = os.path.basename(path)
    folder_prefix = os.path.basename(os.path.dirname(path))
    folderpath = os.path.join(output_folder, folder_prefix)
    filepath = os.path.join(folderpath, filename)
    dicom_dicts[path]['new_path'] = filepath
    dicom_dicts[path]['orig_path'] = path
    dicom_dicts[path]['generate_uid'] = generate_uid # Remember, the action found in deid.dicom is "REPLACE StudyInstanceUID func:generate_uid" so the key here needs to be "generate_uid"
    if save_to_elastic and input_range: 
      dicom_dicts[path]['_id'] = str(doc_ids[idx]) # Store elasticsearch document id so it has the same ID in a new index

  t0 = time.time()

  # MAIN LOOP: Process each dicom
  for dicom_path, dicom_dict in dicom_dicts.items():
    log.debug('Processing DICOM path: %s' % path)
    item = {dicom_path: dicom_dict}

    # De-Identify Metadata (and link it)
    log.info('De-identifying DICOM header...')
    cleaned_files = replace_identifiers(dicom_files=dicom_path,
                                        deid=recipe,
                                        ids=item,
                                        save=False,
                                        remove_private=False)
                                        # overwrite=True,
                                        # output_folder=output_folder)
    
    cleaned_header_dicom = cleaned_files[0] # we only pass in one at a time

    # Create output folder
    filename = os.path.basename(dicom_path)
    folder_prefix = os.path.basename(os.path.dirname(dicom_path))
    folderpath = os.path.join(output_folder, folder_prefix)
    output_filepath = os.path.join(folderpath, filename)
    if not os.path.exists(folderpath):
        log.info('Creating output folder: %s' % folderpath)
        os.makedirs(folderpath)

    # Add derived fields
    cleaned_header_dicom = add_derived_fields(cleaned_header_dicom)

    # Process pixels (de-id pixels and save debug gif)
    if not no_pixels:
      cleaned_pixels_dicom = process_pixels(dicom_path, output_filepath) # note this opens the dicom again (in a way that can access pixels) and thus contains PHI
      get_report_as_dict(cleaned_pixels_dicom) 

    ## Process Radiology Text Report
    #embed()
      report_raw = cleaned_pixels_dicom.get('0x0019, 0x0030')
      if ( report_raw != None):
        PHI = get_PHI(cleaned_pixels_dicom)
        PHI.append('2035.02.15')
        for item in PHI:
          if item in report_raw:
            UID = generate_uid()
            report_raw.replace(item, UID)
      # set in dicom
      # save report to disk

    # if path to radiology report exists in cleaned_header_dicom then...
    #   get the report text from cleaned_header_dicom, find strings given a list of PHI (get_PHI(dicom)) and replace with from UID from generate_uid(), and then save the de-id report to a file on disk

    # Store derived data in DICOM
      cleaned_header_dicom.PatientAge = cleaned_pixels_dicom.get('PatientAge')

    # TODO: UNCOMMENT!
    # Store updated pixels in DICOM
    # if cleaned_header_dicom.file_meta.TransferSyntaxUID.is_compressed:
    #   cleaned_header_dicom.decompress()
    # cleaned_header_dicom.PixelData = dicom.PixelData

    # Save DICOM to disk
    cleaned_header_dicom.save_as(output_filepath)
    log.info('Saved DICOM: %s' % output_filepath)

  # Print Summary
  elapsed_time = time.time() - t0
  ingest_rate = len(dicom_dicts) / elapsed_time
  log.info('{} documents processed '.format(len(dicom_dicts)) + 'in {:.2f} seconds.'.format(elapsed_time))
  log.info('Processing rate (documents/s): {:.2f}'.format(ingest_rate))
  log.info('Finished.')
