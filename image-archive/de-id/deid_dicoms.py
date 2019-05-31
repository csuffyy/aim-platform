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
# OR
# python3.5 deid_dicoms.py --input_file /home/dan/823-whole-body-MR-with-PHI.dcm --output_folder ./tmp/ --fast_crop
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
MATCH_CONF_THRESHOLD = 50
TOO_MUCH_TEXT_THRESHOLD = 0
log.info("Settings: %s=%s" % ('ELASTIC_IP', ELASTIC_IP))
log.info("Settings: %s=%s" % ('ELASTIC_PORT', ELASTIC_PORT))
log.info("Settings: %s=%s" % ('INDEX_NAME', INDEX_NAME))
log.info("Settings: %s=%s" % ('DOC_TYPE', DOC_TYPE))
log.info("Settings: %s=%s" % ('LINKING_INDEX_NAME', LINKING_INDEX_NAME))
log.info("Settings: %s=%s" % ('LINKING_DOC_TYPE', LINKING_DOC_TYPE))
log.info("Settings: %s=%s" % ('RESIZE_FACTOR', RESIZE_FACTOR))
log.info("Settings: %s=%s" % ('MATCH_CONF_THRESHOLD', MATCH_CONF_THRESHOLD))
log.info("Settings: %s=%s" % ('TOO_MUCH_TEXT_THRESHOLD', TOO_MUCH_TEXT_THRESHOLD))


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
  log.info('Got pixels of shape: %s TransferSyntaxUID: %s' % (str(img.shape), dicom.file_meta.TransferSyntaxUID))
  if len(img.shape) not in [2,3]:
    # TODO: Support 3rd physical dimension, z-slices. Assuming dimenions x,y,[color] from here on.
    log.warning('Skipping image becasue shape is not 2d-grey or rgb: %s' % filename)
    return
  if len(img.shape) == 3 and img.shape[2] != 3:
    log.warning('Skipping image becasue shape is z-stack: %s' % filename)
    return

  # Crop the image to 100x100 just for fast algorithm testing
  if fast_crop:
    img = img[0:100, 0:133]

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

def get_PHI():
  """ Note: there may be more PHI values than keys because we split name into several values and look for each seperately """
  PHI = list(found_PHI.values())

  # Split PatientName into parts, each part is PHI
  if 'PatientName' in found_PHI:
    name_parts = re.split('\^| ',str(found_PHI['PatientName'])) # PatientName is typically: FirstName^LastName
    PHI.extend(name_parts)

  # Ensure upper case
  PHI = [x.upper() for x in PHI if x is not None] 

  if len(PHI) == 0:
    log.warning('Returning no PHI.')

  return PHI

def ocr(img, ocr_num=None):
  log.info('Starting OCR...')
  # Do OCR
  tesseract_config = '--oem %d --psm 3' % ocr_num
  detection = pytesseract.image_to_data(img,config=tesseract_config, output_type=pytesseract.Output.DICT)
  detection = pd.DataFrame.from_dict(detection) # convert to dataframe
  detection = detection[detection.text != ''] # remove empty strings

  log.info('OCR Found %d blocks of text' % len(detection))
  if detection.empty:
    log.warning('No text found by OCR')

  return detection

def match(search_strings, detection, ocr_num=None):
  if detection.empty or search_strings is None or search_strings == []:
    return detection

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
      if match_conf > MATCH_CONF_THRESHOLD:
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

def clean_pixels(dicom, img_orig, detection, output_filepath, input_filepath, is_mostly_text, amount_of_text_score):
  """ Put black boxes in image to "clean" it """
  removals = []
  yellow = 'rgb(255, 255, 0)' # yellow color
  black = 'rgb(0, 0, 0)' # yellow input_color
  dicom_pixels = dicom.pixel_array

  img_dtype = str(img_orig.dtype)

  # Work-around for Pillow which doesn't support 16bit images
  # https://github.com/python-pillow/Pillow/issues/2970
  if 'uint16' == img_dtype:
    cv2.normalize(img_orig, img_orig, 0, 255, cv2.NORM_MINMAX)
    # img_orig = img_orig.astype('uint16')
    # image_orig = Image.fromarray(img_orig)
    # image_PHI = Image.fromarray(img_orig)
    array_buffer = img_orig.tobytes()
    image_orig = Image.new("I", img_orig.T.shape)
    image_orig.frombytes(array_buffer, 'raw', "I;16")
    array_buffer = img_orig.tobytes()
    image_PHI = Image.new("I", img_orig.T.shape)
    image_PHI.frombytes(array_buffer, 'raw', "I;16")
  elif 'int16' == img_dtype:
    # Pillow fully doesn't support u16bit images! eek. TODO: Find a way to preserve 16 bit precision. I tried a bunch of stuff but couldn't preserve appearent constrast
    cv2.normalize(img_orig, img_orig, 0, 255, cv2.NORM_MINMAX)
    img_orig = img_orig.astype('uint16')
    array_buffer = img_orig.tobytes()
    image_orig = Image.new("I", img_orig.T.shape)
    image_orig.frombytes(array_buffer, 'raw', "I;16")
    array_buffer = img_orig.tobytes()
    image_PHI = Image.new("I", img_orig.T.shape)
    image_PHI.frombytes(array_buffer, 'raw', "I;16")
  else:
    # Let Pillow Decide
    image_orig = Image.fromarray(img_orig)
    image_PHI = Image.fromarray(img_orig)

  # For debugging purposes, image_PHI is the image with detected PHI overlaid annotations, draw_PHI is a helper object for annotating. It will be used in a gif
  draw_PHI = ImageDraw.Draw(image_PHI)

  # For debugging purposes, image_all_txt is the image with all detected text overlaid annotations, draw_all_txt is a helper object for annotating. It will be used in a gif
  image_all_txt = image_PHI.copy()
  draw_all_txt = ImageDraw.Draw(image_all_txt)

  # Draw Annotations
  for index, row in detection.iterrows():
    top = row.top
    left = row.left
    height = row.height
    width = row.width
    ocr_text = row.text
    ocr_conf = row.conf
    match_conf = row.match_conf
    match_text = row.match_text

    # Black out in actual dicom pixels
    if row.match_bool:
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
    draw_all_txt.rectangle(xy, fill=black, outline=yellow)
    draw_all_txt.multiline_text((left, top), annotation, fill=yellow, font=font)
    if row.match_bool:
      draw_PHI.rectangle(xy, fill=black, outline=yellow)
      draw_PHI.multiline_text((left, top), annotation, fill=yellow, font=font)

    # Store removal details
    if row.match_bool:
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

  # Debug info for amount of text
  width = img_orig.shape[1]
  # height = 16
  height = int(14*img_orig.shape[1]/120/RESIZE_FACTOR)+4
  left = 0
  top = img_orig.shape[0]-height
  xy = [left, top, left+width, top+height]
  choice_str = 'REJECT' if is_mostly_text else 'ACCEPT'
  filename = os.path.basename(input_filepath)
  annotation = ' %s, %d text score, %s, %s' % (filename, amount_of_text_score, img_dtype, choice_str)
  metadata_fontsize = int(14*img_orig.shape[1]/120/RESIZE_FACTOR)
  font = ImageFont.truetype('Roboto-Regular.ttf', size=metadata_fontsize)
  draw_PHI.rectangle(xy, fill=black, outline=yellow)
  draw_PHI.multiline_text((left, top), ' PHI' + annotation, fill=yellow, font=font, align='left')
  draw_all_txt.rectangle(xy, fill=black, outline=yellow)
  draw_all_txt.multiline_text((left, top), ' ALL' + annotation, fill=yellow, font=font, align='left')

  if len(removals)==0:
    log.warning('No detected text closely matches the PHI: %s' % input_filepath)

  # Display
  if display_on_screen:
    matplotlib.use('TkAgg')
    image_PHI.show()
  if save_gifs:
    matplotlib.use('Agg')
    image_orig = image_orig.convert('RGB')
    image_PHI = image_PHI.convert('RGB')
    image_all_txt = image_all_txt.convert('RGB')
    frames = [image_all_txt, image_PHI, image_orig]
    frames[0].save('%s.gif' % output_filepath, format='GIF', append_images=frames[1:], save_all=True, duration=2222, loop=0)
    log.info('Saved GIF: %s.gif' % output_filepath)

  # Store updated pixels in DICOM
  dicom = decompress_dicom(dicom)
  dicom.PixelData = dicom_pixels.tobytes()

  return (dicom, removals)

def decompress_dicom(dicom):
  if dicom.file_meta.TransferSyntaxUID.is_compressed:
    try:
      dicom.decompress()
    except:
      log.warning('Failed to decompress dicom.')
  return dicom

def amount_of_text(detection):
  # TODO: Normalize by image resolution

  # Score amount of text
  score = 0
  for index, row in detection.iterrows():
    score += row.conf*len(row.text) # the amount of text is scored by multiply the number of characters by the confidence of the detected text block

  # Check if amount of text is greater than threshold
  is_mostly_text = False
  if score > TOO_MUCH_TEXT_THRESHOLD:
    is_mostly_text = True

  return (is_mostly_text, score)

def process_pixels(input_filepath, output_filepath):
  # Get Pixels
  ret = get_pixels(input_filepath)
  if ret is None:
    return
  img_bw, img_orig, dicom = ret

  # Preprocess Pixels (Variety #1)
  log.info('Processing 1...')
  img_enhanced = tophat_proprocess(img_bw)

  # Detect Text with OCR
  detection = ocr(img_enhanced, ocr_num=2)

  # Detect if image has so much text that it's probably a requisition and should be rejected or so little text that it should be accepted without PHI matching

  # Score if this image has too much text
  is_mostly_text, amount_of_text_score = amount_of_text(detection)

  # Match Detected Text to PHI
  log.info('Matching 1...')
  detection = match(get_PHI(), detection, ocr_num=2)

  if ocr_fallback_enabled:
    # Preprocess Pixels (Variety #2)
    log.info('Processing 2...')
    img_enhanced = blur_sharpen_preprocess(img_bw)

    # Detect Text with OCR
    detection2 = ocr(img_enhanced, ocr_num=2)

    # Match Detected Text to PHI
    log.info('Matching 2...')
    detection2 = match(get_PHI(), detection2, ocr_num=2)

    # Combine detection results of different preprocessing
    detection = pd.concat([detection, detection2], ignore_index=True, sort=True)

  # Clean Image Pixels
  dicom, removals = clean_pixels(dicom, img_orig, detection, output_filepath, input_filepath, is_mostly_text, amount_of_text_score)
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
  uid = str(uuid.uuid4()) # otherwise generate new id
  orig = dicom_dict[field_name] if field_name in dicom_dict else ''
  if orig == '':
    return ''

  # Look to find existing linking in ElasticSearch
  if save_to_elastic:
    res = lookup_linking(orig)

    if len(res):
      # Found existing in elastic, use id already generated
      uid = res[0]['_source']['new']
    else:
      # otherwise insert a new linking for this unseen original value to a uid
      query = {'orig': orig, 'new': uid, 'field': field_name, 'date': datetime.datetime.now(), 'orig_path': dicom_dict['orig_path'], 'new_path': dicom_dict['new_path']}
      if '_id' in dicom_dict:
        query['id'] = dicom_dict['_id'] # Use same elasticsearch document ID from input index in the new index
      res = es.index(body=query, index=LINKING_INDEX_NAME, doc_type=LINKING_DOC_TYPE)

    log.debug('Linking %s:%s-->%s' % (field_name, orig, uid))

  # Keep track of what PHI was found
  found_PHI[field_name] = orig

  return uid

def get_report_as_dict(cleaned_pixels_dicom):
  report_dict = {}
  hex_list = [0x0019, 0x0030]
  report_part = cleaned_pixels_dicom.get(hex_list)
  while(report_part is not None):
    seperate_key_value = report_part.value.split(": ")
    report_dict[seperate_key_value[0][7:].strip()] = ":".join(seperate_key_value[1:]) #7 means the end of the word report

    #icrements the hexidecimal values and replaces the hex string
    hex_list[1] += 1
    #gets the next values for the next possible key and value in the dictionary
    report_part = cleaned_pixels_dicom.get(hex_list)

  return report_dict

"""
@param known_dates: a list of strings of dates
@param text: the block of text that will be searched for dates
@return Returns if each date in known_dates is in text in the form or a list of booleans
"""
def datematcher(known_dates, text):

  returning = []

  matches = datefinder.find_dates(text, source=True, index=True)
  matches = list(matches)

  for date in known_dates:
    datetime_object = datefinder.find_dates(date) #gets the datetime object of date
    datetime_object = list(datetime_object)

    if datetime_object != []: #there was a date at that PHI position
      for txt_day in matches:
        if datetime_object[0] in txt_day: #if the date matches one of the text
          returning.append(txt_day[1]) #append the line of text where the dates matched

  return returning

#
def match_date_and_exact(cleaned_pixels_dicom, field_tag):
  field_val = cleaned_pixels_dicom.get(field_tag)
  #print(field_val.value)
  if (field_val != None): #check if the field exists
    PHI = get_PHI()
    PHI.append('2034.06.20')
    PHI.append('2019.05.01')
    PHI.append('2035/02/16')
    PHI.append('11.02.35')
    PHI.append('2035/02/15')
    PHI.append('PLAST')
    PHI.append('PFIRST')

    exact_match_list = []
    indirect_match_list = []

    for element in PHI:
      if element in field_val.value: #meaning that that element can be directly replaced
        exact_match_list.append(element)
      else: #the element cannot be direclty replaced
        indirect_match_list.append(element)

    if exact_match_list != []: #there are exact matches
      field_val.value = match_exact(cleaned_pixels_dicom, field_tag, exact_match_list)


    if indirect_match_list != []: #there are PHI still left to check after exact matches
      field_val.value = match_indirect(cleaned_pixels_dicom, field_tag, indirect_match_list)

    #save the edited dicom to the specified file
    save_to_file(cleaned_pixels_dicom)


def match_exact(cleaned_pixels_dicom, field_tag, match_list):
  dicom_field = cleaned_pixels_dicom.get(field_tag)
  field_val = dicom_field.value

  for element in match_list:
    element_dt_obj = datefinder.find_dates(element)
    element_dt_obj = list(element_dt_obj)
    if element_dt_obj == []: #is not a date
        _dict = {'key': element, 'new_path': output_filepath, 'orig_path': dicom_path}
    else: #is a date
        _dict = {'key': element_dt_obj[0].strftime('%Y/%m/%d'), 'new_path': output_filepath, 'orig_path': dicom_path}

    UID = generate_uid(_dict, 'nope', 'key')
    field_val = field_val.replace(element, str(UID))

  return field_val

#maches PHI dates that were not the exact same format as those found in the dicom
def match_indirect(cleaned_pixels_dicom, field_tag, match_list):
  dicom_field = cleaned_pixels_dicom.get(field_tag) 
  field_val = dicom_field.value

  indirect_dates = datematcher(match_list, field_val)

  for indirect_day in indirect_dates: #check where the date is and replace it 
    split_day = re.split('[ :]', indirect_day)
    for split_piece in split_day:
      split_dt_obj = datefinder.find_dates(split_piece, source= True)
      split_dt_obj = list(split_dt_obj)

      if split_dt_obj != []: #if a date was found
        _dict = {'key': split_dt_obj[0][0].strftime('%Y/%m/%d'), 'new_path': output_filepath, 'orig_path': dicom_path}
        UID = generate_uid(_dict, 'nope', 'key')
        field_val = field_val.replace(split_dt_obj[0][1], str(UID))

  return field_val

def save_to_file(cleaned_pixels_dicom): #save the edited dicom to the specified file given in the dicom

  report_dict = get_report_as_dict(cleaned_pixels_dicom) 

  file_to_save = report_dict['filepath']
  filename = os.path.basename(file_to_save)
  filename = 'deid' + filename
  folder_prefix = os.path.basename(os.path.dirname(file_to_save))
  output_filepath_dict = os.path.join(folderpath, filename)

  file_to_write = open(output_filepath_dict, 'w')
  file_to_write.write(str(report_dict['Raw']))
  file_to_write.close()

if __name__ == '__main__':
  # Set up command line arguments
  parser = argparse.ArgumentParser(description='Looks up documents in ElasticSearch, finds the DICOM files, processes them, and saves a copy.')
  parser.add_argument('--input_range', help='Positional document numbers in ElasticSearch (ex. 1-10). These documents will be processed.')
  parser.add_argument('--input_files', help='Pass in file that contains list of DICOM files which will be processed.')
  parser.add_argument('--input_file', help='Pass in a single DICOM file by giving path on disk.')
  parser.add_argument('--no_elastic', action='store_true', help='Skip saving metadata to ElasticSearch.')
  parser.add_argument('--no_pixels', action='store_true', help='Skip de-identification of pixels.')
  parser.add_argument('--deid_recipe', default='deid.dicom', help='De-id rules.')
  parser.add_argument('--output_folder', help='Save processed DICOM files to this path.')
  parser.add_argument('--input_dicom_filename', help='Process only this DICOM by name (looked up in ElasticSearch)')
  parser.add_argument('--ocr_fallback_enabled', action='store_true', help='Only try one pass of OCR to find PHI')
  parser.add_argument('--fast_crop', action='store_true', help='Crop the image to 100x100 just for fast algorithm testing')
  parser.add_argument('--screen', action='store_true', help='Display output pixels on screen')
  parser.add_argument('--gifs', action='store_true', help='Save output pixels to gifs')
  args = parser.parse_args()
  output_folder = args.output_folder
  save_to_elastic = not args.no_elastic
  ocr_fallback_enabled = args.ocr_fallback_enabled
  fast_crop = args.fast_crop
  no_pixels = args.no_pixels
  input_dicom_filename = args.input_dicom_filename
  input_range = args.input_range
  input_files = args.input_files
  input_file = args.input_file
  deid_recipe = args.deid_recipe
  display_on_screen = args.screen
  save_gifs = args.gifs
  log.info("Settings: %s=%s" % ('output_folder', output_folder))
  log.info("Settings: %s=%s" % ('save_to_elastic', save_to_elastic))
  log.info("Settings: %s=%s" % ('no_pixels', no_pixels))
  log.info("Settings: %s=%s" % ('input_dicom_filename', input_dicom_filename))
  log.info("Settings: %s=%s" % ('input_range', input_range))
  log.info("Settings: %s=%s" % ('input_files', input_files))
  log.info("Settings: %s=%s" % ('input_file', input_file))
  log.info("Settings: %s=%s" % ('deid_recipe', deid_recipe))
  log.info("Settings: %s=%s" % ('ocr_fallback_enabled', ocr_fallback_enabled))
  log.info("Settings: %s=%s" % ('fast_crop', fast_crop))
  log.info("Settings: %s=%s" % ('display_on_screen', display_on_screen))
  log.info("Settings: %s=%s" % ('save_gifs', save_gifs))

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
  elif input_file:
    dicom_paths = [input_file]
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
    size = input_end - input_start + 1
    query = {
      "_source": ["_id", "dicom_filepath"],
      "from": input_start,
      "size": size,
    }
  # Actually get documents from ElasticSearch
  if input_dicom_filename or input_range:
    results = es.search(body=query, index=INDEX_NAME)
    log.info("Number of Search Hits: %d" % len(results['hits']['hits']))
    results = results['hits']['hits']
    dicom_paths = [res['_source']['dicom_filepath'] for res in results]
    doc_ids = [res['_id'] for res in results]

  log.info("Number of input files: %d" % len(dicom_paths))
  t0 = time.time()

  # MAIN LOOP: Process each dicom
  for idx, dicom_path in enumerate(dicom_paths):
    log.info('Processing DICOM path: %s' % dicom_path)

    # Setup
    found_PHI = {}

    # Prepare to De-Identify Metadata
    dicom_dict = get_identifiers([dicom_path])
    filename = os.path.basename(dicom_path)
    folder_prefix = os.path.basename(os.path.dirname(dicom_path))
    folderpath = os.path.join(output_folder, folder_prefix)
    filepath = os.path.join(folderpath, filename)
    dicom_dict[dicom_path]['new_path'] = filepath
    dicom_dict[dicom_path]['orig_path'] = dicom_path
    dicom_dict[dicom_path]['generate_uid'] = generate_uid # Remember, the action found in deid.dicom is "REPLACE StudyInstanceUID func:generate_uid" so the key here needs to be "generate_uid"
    if save_to_elastic and input_range: 
      dicom_dict[dicom_path]['_id'] = str(doc_ids[idx]) # Store elasticsearch document id so it has the same ID in a new index
    # De-Identify Metadata (and keep track of value replacements ie. linking) (and this will populate the found_PHI global variable)
    log.info('De-identifying DICOM header...')
    cleaned_files = replace_identifiers(dicom_files=dicom_path,
                                        deid=recipe,
                                        ids=dicom_dict,
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
      if cleaned_pixels_dicom is None:
        log.warning('Couldnt read pixels so skipping: %s' % dicom_path)
        continue

      # Save de-ided PHI into "cleaned_pixels_dicom" variable, this variable is the full dicom but cleaned_header_dicom is not
      for key in found_PHI.keys():
        cleaned_pixels_dicom.data_element(key).value = cleaned_header_dicom.data_element(key).value

      # Look for detected PHI in fields outside of expected fields
      for field in cleaned_pixels_dicom.iterall():
        # Skip pixel data
        if field.name == 'Pixel Data':
          continue
        # Skip objects of this kind because they can't be made into strings, perhaps go deeper
        if field.value.__class__ == pydicom.sequence.Sequence:
          continue

          # field.tag

        #cleaned_pixels_dicom = replace_PHI(cleaned_pixels_dicom, field, get_PHI())
        #   OLD_VALUE = str(field.value)
        #   # replace PHI with uid
        #   field.value = NEW_VALUE
        #   cleaned_pixels_dicom.__setitem__(field.tag, field)
        # Note: Make sure case doesn't matter when doing matching (force upper case. note that get_PHI() returns only upper case)
        # Note: Only match when number of characters is >=5. Reason being we dont to make lots of deteles if a common word like "the" slips into the PHI but on the other hand what about short names? The OCR matching currently requires 2 charaters or more
        # TODO(Dan): see how match() OCR can utilize find_and_replace_PHI()
        # TODO(Dan):  match() OCR should try matching to substrings of longer blocks of text, split on seperators, which? just space or .-/\+_ ? 

      print(field.tag)
      match_date_and_exact(cleaned_pixels_dicom, [0x0019, 0x0030])


#---------------------------------OLD CODE-------------------------------------------------

      # ## Process Radiology Text Report
      # report_raw = cleaned_pixels_dicom.get([0x0019, 0x0030])
      # if (report_raw != None): #check if the report exists

      #   PHI = get_PHI()
      #   PHI.append('2034.06.20')
      #   PHI.append('2019.05.01')
      #   PHI.append('2035/02/16')
      #   PHI.append('11.02.35')
      #   PHI.append('2035/02/15')
      #   PHI.append('PLAST')
      #   PHI.append('PFIRST')

      #   date_edit_possible = []

      #   for element in PHI:
      #     if element in report_raw.value: #if the element is written explcitly in the raw report, replace
      #       element_dt_obj = datefinder.find_dates(element)
      #       element_dt_obj = list(element_dt_obj)
      #       if element_dt_obj == []: #is not a date
      #         _dict = {'key': element, 'new_path': output_filepath, 'orig_path': dicom_path}
      #       else: #is a date
      #         _dict = {'key': element_dt_obj[0].strftime('%Y/%m/%d'), 'new_path': output_filepath, 'orig_path': dicom_path} 
            
      #       UID = generate_uid(_dict, 'nope', 'key')
      #       report_raw.value = report_raw.value.replace(element, str(UID))
      #     else:
      #         date_edit_possible.append(element)

      #   if date_edit_possible != []: #there are some elements from PHI list that may just be styled incorrectly
      #     indirect_dates = datematcher(date_edit_possible, report_raw.value)

      #     for indirect_day in indirect_dates: #check where the date is and replace it 
      #       split_day = re.split('[ :]', indirect_day)
      #       for split_piece in split_day:
      #         split_dt_obj = datefinder.find_dates(split_piece, source= True)
      #         split_dt_obj = list(split_dt_obj)

      #         if split_dt_obj != []: #if a date was found
      #           _dict = {'key': split_dt_obj[0][0].strftime('%Y/%m/%d'), 'new_path': output_filepath, 'orig_path': dicom_path}
      #           UID = generate_uid(_dict, 'nope', 'key')
      #           report_raw.value = report_raw.value.replace(split_dt_obj[0][1], str(UID))

      #   print('\n\n\n\n\n\n\n\n\n\n')
      #   print(report_raw.value)


      #   #THIS FOR SURE WORKS - saves the raw report to a file
      #   report_dict = get_report_as_dict(cleaned_pixels_dicom)

      #   file_to_save = report_dict['filepath']
      #   filename = os.path.basename(file_to_save)
      #   filename = 'deid' + filename
      #   folder_prefix = os.path.basename(os.path.dirname(file_to_save))
      #   output_filepath_dict = os.path.join(folderpath, filename)

      #   file_to_write = open(output_filepath_dict, 'w')
      #   file_to_write.write(str(report_dict['Raw']))
      #   file_to_write.close()


#---------------------------------OLD CODE-------------------------------------------------

#    # # Store derived data in DICOM
#    # TODO: DELETE - COMMENTED out because it's already in cleaned_pixels
#    # cleaned_header_dicom.PatientAge = cleaned_pixels_dicom.get('PatientAge')
#
#    # # Store updated pixels in DICOM
#    # TODO: DELETE - COMMENTED out because it's already in cleaned_pixels
#    # cleaned_header_dicom = decompress_dicom(cleaned_header_dicom)
#    # cleaned_header_dicom.PixelData = cleaned_pixels_dicom.PixelData

    # Save DICOM to disk
    try:
      cleaned_pixels_dicom.save_as(output_filepath)
      log.info('Saved DICOM: %s' % output_filepath)
    except Exception as e:
      print(traceback.format_exc())
      log.error('Failed to save de-identified dicom to disk: %s\n' % filepath)
      if 'Pixel Data with undefined length must start with an item tag' in str(e):
        cleaned_pixels_dicom[(0x7fe0,0x0010)].is_undefined_length = False
        cleaned_pixels_dicom.save_as(output_filepath)
        log.error('Successfully recovered from error and saved de-identified dicom to disk: %s\n' % filepath)

  # Print Summary
  elapsed_time = time.time() - t0
  ingest_rate = len(dicom_paths) / elapsed_time
  log.info('{} documents processed '.format(len(dicom_paths)) + 'in {:.2f} seconds.'.format(elapsed_time))
  log.info('Processing rate (documents/s): {:.2f}'.format(ingest_rate))
  log.info('Finished.')
