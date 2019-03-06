#!/bin/python
#. /home/dan/python3.7venv/bin/activate
#python /home/dan/pixel_deidentify/main3.py
import os
import re
import cv2
import time
import pickle
import pydicom
import matplotlib
import pytesseract
import collections
import numpy as np
import pandas as pd

from IPython import embed
from fuzzywuzzy import fuzz
from itertools import chain
from datetime import datetime
from fuzzywuzzy import process
from matplotlib import pyplot as plt
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dateutil.relativedelta import relativedelta
from skimage.morphology import white_tophat, disk

import logging
logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
log = logging.getLogger('main')
log.info('Starting Pixel De-Identify')

input_folder = '/home/dan/Two_Images'
input_folder = '/home/dan/Pictures/Spikey'
input_folder = '/home/dan/Pictures/US'
RESIZE_FACTOR = 4 # how much to blow up image to make OCR work better
MATCH_CONF_THRESH = 50
OUTPUT = 'screen'
OUTPUT = 'gifs'
OUTPUT = 'dcm'
no_plot = False
no_plot = True
only_one = '88179052.dcm'
only_one = None
datestr = time.strftime('%Y%m%d-%H%M%S')
output_path = '/home/dan/pixel_deidentify/plots/%s' % datestr

if OUTPUT == 'screen':
  matplotlib.use('TkAgg')
elif OUTPUT in ['gifs', 'dcm']:
  matplotlib.use('Agg')

def plot_comparison(original, filtered, filter_name):
  fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(8, 4), sharex=True,
                                 sharey=True)
  ax1.imshow(original, cmap=plt.cm.gray)
  ax1.set_title('original')
  ax1.axis('off')
  # ax1.axis('tight')
  ax2.imshow(filtered, cmap=plt.cm.gray)
  ax2.set_title(filter_name)
  ax2.axis('off')
  # ax2.axis('tight')


def flatten(l):
  for el in l:
    if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
      yield from flatten(el)
    else:
      yield el

def calc_timing_stats(times_per_image):
  ## Calculate Timing Statistics
  times_df = pd.DataFrame()
  # Compute time differences for each time step for each image
  for times in times_per_image:
    times_row = pd.DataFrame()
    time_step_names = [key.replace('_before', '') for key in times.keys() if '_before' in key]
    for name in time_step_names:
      diff_datetime, diff_string = time_diff(times['%s_before' % name], times['%s_after' % name])
      times_row[name] = [diff_datetime.microseconds]
    times_df = times_df.append(times_row)

  if no_plot:
    return

  plt.clf()
  ax = times_df.boxplot()
  ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
  # ax.set_yscale('log')
  plt.legend(loc='best')
  if OUTPUT == 'screen':
    plt.show()
  elif OUTPUT in ['gifs','dcm']:
    plt.savefig('%s_timing.png' % output_path)

def orc(metadata, image, times, ocr_num=None):
  times['ocr%d_before' % ocr_num] = datetime.now()
  # Do OCR
  tesseract_config = '--oem %d --psm 3' % ocr_num
  detection = pytesseract.image_to_data(image,config=tesseract_config, output_type=pytesseract.Output.DICT)
  detection = pd.DataFrame.from_dict(detection) # convert to dataframe
  detection = detection[detection.text != ''] # remove empty strings

  times['ocr%d_after' % ocr_num] = datetime.now()
  if detection.empty:
    log.warning('No text found by OCR')
    return detection

  metadata['ocr%d_detection' % ocr_num] = [detection]
  return detection

def match(metadata, search_strings, detection, times, ocr_num=None):
  if detection.empty:
    return

  times['match%d_before' % ocr_num] = datetime.now()
  match_confs = []
  match_texts = []
  match_bool = []
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
  times['match%d_after' % ocr_num] = datetime.now()

def pixel_deidentify(dicom, img, im_resized, detection, times, ocr_num=None):
  times['pixel_deidentify%d_before' % ocr_num] = datetime.now()
  removals = []

  image = Image.fromarray(im_resized)
  draw = ImageDraw.Draw(image)
  yellow = 'rgb(255, 255, 0)' # yellow color
  black = 'rgb(0, 0, 0)' # yellow color
  
  im_orig = cv2.resize(img, dsize=(img.shape[1]*RESIZE_FACTOR, img.shape[0]*RESIZE_FACTOR), interpolation=cv2.INTER_CUBIC)
  image_orig = Image.fromarray(im_orig)
  draw_orig = ImageDraw.Draw(image_orig)
  image_color = Image.fromarray(im_orig)
  draw_color = ImageDraw.Draw(image_color)

  dicom_pixels = dicom.pixel_array

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

      annotation = 'ocr: %s, %d\nmatch: %s, %d' % (ocr_text, ocr_conf, match_text, match_conf)

      xy = [left, top, left+width, top+height]
      font = ImageFont.truetype('/home/dan/pixel_deidentify/fonts/Roboto-Regular.ttf', size=int(height/2.5))
      draw.rectangle(xy, fill=black, outline=yellow)
      draw.multiline_text((left, top), annotation, fill=yellow, font=font)

      draw_color.rectangle(xy, fill=black, outline=yellow)
      draw_color.multiline_text((left, top), annotation, fill=yellow, font=font)

      # Black out in actual dicom pixels (saving my PIL de-id'd image into the DICOM is giving me trouble)
      if OUTPUT == 'dcm':
        sml_left = int(left / RESIZE_FACTOR)
        sml_top = int(top / RESIZE_FACTOR)
        sml_width = int(width / RESIZE_FACTOR)
        sml_height = int(height / RESIZE_FACTOR)
        dicom_pixels[sml_top:sml_top+sml_height, sml_left:sml_left+sml_width] = 0
        dicom_pixels[sml_top, sml_left:sml_left+sml_width] = np.max(dicom_pixels)
        dicom_pixels[sml_top+sml_height, sml_left:sml_left+sml_width] = np.max(dicom_pixels)
        dicom_pixels[sml_top:sml_top+sml_height, sml_left] = np.max(dicom_pixels)
        dicom_pixels[sml_top:sml_top+sml_height, sml_left+sml_width] = np.max(dicom_pixels)

        # sml = image.resize((img.shape[1], img.shape[0]), Image.ANTIALIAS)
        # pix = np.array(sml)
        # dicom.PixelData = pix.tobytes()
      

      # Store
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
    log.warning('No detected text closely matches the PHI: %s' % filename)

  times['pixel_deidentify%d_after' % ocr_num] = datetime.now()

  times['save%d_before' % ocr_num] = datetime.now()
  # Save to disk
  if OUTPUT == 'screen':
    image.show()
  elif OUTPUT == 'dcm':
    if dicom.file_meta.TransferSyntaxUID.is_compressed:
      dicom.decompress()
    filepath = '%s_%s_deid.dcm' % (output_path, filename)
    dicom.PixelData = dicom_pixels.tobytes()
    dicom.save_as(filepath)
    log.info('Saved de-id dicom to: %s' % filepath)
  elif OUTPUT == 'gifs':
    # plot_comparison(im_orig, np.array(image_color), 'Processed')
    # plt.savefig('%s_compare.png' % output_path, dpi=400)
    times['save_vis%d_before' % ocr_num] = datetime.now()
    image = image.convert('RGB')
    # image.save('%s_%s_vis.png' % (output_path, filename), optimize=True) # PNG
    # image.save('%s_%s_vis.jpg' % (output_path, filename)) # JPG processed
    # image_color.save('%s_%s_vis.jpg' % (output_path, filename)) # JPG original redacted
    # image_orig.save('%s_%s_vis-orig.jpg' % (output_path, filename)) # JPG original
    frames = [image_color, image_orig]
    frames[0].save('%s_%s_vis.gif' % (output_path, filename), format='GIF', append_images=frames[1:], save_all=True, duration=1000, loop=0)
    times['save_vis%d_after' % ocr_num] = datetime.now()
  times['save%d_after' % ocr_num] = datetime.now()
  return removals

def time_diff(t_a, t_b):
  from dateutil.relativedelta import relativedelta
  t_diff = relativedelta(t_b, t_a)  # later/end time comes first!
  return t_diff, '{h}h {m}m {s}s {ms}ms'.format(h=t_diff.hours, m=t_diff.minutes, s=t_diff.seconds, ms=t_diff.microseconds/1000)

PHI_found = 0
def calc_stats(removals):
  global PHI_found
  PHI_found += len(removals)

def save_stats():
  global PHI_found
  PHI_actual = 5 # MANUALLY COUNTED
  accuracy = PHI_found / PHI_actual

  # Print Stats to Console
  log.info('Correctly identified PHI: %d/%d (%.1f%%)' % (PHI_found, PHI_actual, accuracy*100))

  # Load Stats
  saved_stats_file = 'saved_stats.pickle'
  stats = pd.DataFrame()
  if os.path.isfile(saved_stats_file):
    stats = pickle.load(open(saved_stats_file, 'rb'))

  # Append Stats
  stat = pd.DataFrame()
  stat['PHI_actual'] = [5]
  stat['PHI_found'] = [PHI_found]
  stat['accuracy'] = [accuracy]
  stat['date'] = [datetime.now()]
  stats = pd.concat([stats, stat], ignore_index=True, sort=True)

  # Plot Stats
  if not no_plot:
    plt.clf()
    fig, ax1 = plt.subplots(num=1)

    color = 'tab:red'
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Count', color=color)
    ax1.plot(stats.date, stats.PHI_found, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('Accuracy (%)', color=color)  # we already handled the x-label with ax1
    ax2.plot(stats.date, stats.accuracy*100, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    fig.tight_layout()  # otherwise the right y-label is slightly clipped

    if OUTPUT == 'screen':
      plt.show()
    elif OUTPUT == 'files':
      plt.savefig('%s_accuracy.png' % output_path)

  # Save Stats
  pickle.dump(stats, open(saved_stats_file, 'wb'))

try:
  # Main code body
  df = pd.DataFrame()
  times_per_image = []
  global filename
  filename = ''

  for subdir, dirs, files in os.walk(input_folder):
    for filename in files:
      times = {}
      filepath =  os.path.join(subdir, filename)
      log.info('Processing: %s' % filepath)

      # Load Image
      times['read_image_before'] = datetime.now()
      dicom = pydicom.dcmread(filepath, force=True)
      # dicom = pydicom.dcmread('/home/dan/Pictures/US/US/88197120.dcm', force=True) # saving is borked by pydicom
      # dicom = pydicom.dcmread('/home/dan/Pictures/US/US/86512662.dcm', force=True) # saving is borked by pydicom
      # dicom = pydicom.dcmread('/home/dan/Pictures/US/US/85683116.dcm', force=True) # saving works with pydicom
      times['read_image_after'] = datetime.now()

      ## Filters
      # one image of interest (for testing only)
      if only_one and filename != only_one:
        continue

      # DICOM Metadata
      if not 'pixel_array' in dicom or not 'PatientName' in dicom or not 'PatientID' in dicom:
        img = dicom.pixel_array
      else:
        log.warning('Required data not found in DICOM: %s' % filename)
        # copyfile(filepath, '%s_%s' % (output_path, filename))
        continue

      # Image shape
      if img.shape == 0:
        log.warning('Image size is 0: %s' % filename)
        # copyfile(filepath, '%s_%s' % (output_path, filename))
        continue
      if len(img.shape) not in [2,3]:
        # TODO: Support 3rd physical dimension, z-slices. Assuming dimenions x,y,[color] from here on.
        log.warning('Image shape is not 2d-grey or rgb: %s' % filename)
        # copyfile(filepath, '%s_%s' % (output_path, filename))
        continue

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

      # Utlrasound Specific (US)
      if dicom.Modality == 'US':
        # Aspect Ratio (US)
        aspect_ratio = img.shape[1] / img.shape[0]
        if not 1.2 < aspect_ratio < 1.6:
          log.warning('Image shape is not expected for ultrasounds: %s (%d,%d)' % (filename, img.shape[0], img.shape[1]))
          # copyfile(filepath, '%s_%s' % (output_path, filename))
          continue

        # Too much white (US)
        num_white_pixels = np.sum(img == 255)
        percent_white_pixels = num_white_pixels / img.size
        if percent_white_pixels > 0.2:
          log.warning('Image has more than 20%% white pixels: %s' % filename)
          # copyfile(filepath, '%s_%s' % (output_path, filename))
          continue

      # Convert to greyscale
      if len(img.shape) == 3:
        img_orig = img
        image = Image.fromarray(img,'RGB')
        image = image.convert('L')
        img = np.array(image)
      else:
        img_orig = img

      ## Preprocess
      times['preprocess_image_before'] = datetime.now()

      # image = Image.fromarray(img,'RGB')
      # image = Image.fromarray(img,'L')
      # image.show()

      # TopHat to strengthen text
      selem = disk(10)
      img = white_tophat(img, selem)

      im_resized = cv2.resize(img, dsize=(img.shape[1]*RESIZE_FACTOR, img.shape[0]*RESIZE_FACTOR), interpolation=cv2.INTER_CUBIC)
      times['preprocess_image_after'] = datetime.now()

      # Build list of PHI to look for: MNR, FirstName, LastName
      name_parts = re.split('\^| ',str(dicom.PatientName)) # PatientName is typically: FirstName^LastName
      PHI = [dicom.PatientID, name_parts]
      PHI = list(flatten(PHI))
      PHI = [x.upper() for x in PHI] # ensure upper case
      dicom_metadata = {}
      [dicom_metadata.__setitem__(key,dicom.get(key)) for key in dicom.dir() if key not in ['PixelData']]

      # Datastructure for this image
      metadata = pd.DataFrame([{'FilePath' : filepath,
                           'Modality' : subdir,
                           'PatientName' : dicom.PatientName,
                           'PatientID' : dicom.PatientID,
                           'PHI' : [PHI],
                           'MetaData' : dicom_metadata,
                         }])

      # OCR, Match, Deidentify
      # detection0 = orc(metadata, im_resized, times, ocr_num=0)
      # match(metadata, PHI, detection0, times, ocr_num=0)
      # detection1 = orc(metadata, im_resized, times, ocr_num=1)
      # match(metadata, PHI, detection1, times, ocr_num=1)
      detection2 = orc(metadata, im_resized, times, ocr_num=2)
      match(metadata, PHI, detection2, times, ocr_num=2)
      # detection = pd.concat([detection0, detection1, detection2], ignore_index=True, sort=True)
      # detection = detection0
      # detection = detection1
      detection = detection2

      # Try more preprocessing if we didn't find as many PHI as expected in ultrasound
      if not np.sum(detection.match_bool) >= len(PHI) and dicom.Modality == 'US':
        log.info('Trying more preprocessing.')
        # Sharpen
        image = Image.fromarray(img,'L')
        image = image.filter( ImageFilter.GaussianBlur(radius=1.5))
        image = image.filter( ImageFilter.EDGE_ENHANCE_MORE )
        img = np.array(image)
        im_resized = cv2.resize(img, dsize=(img.shape[1]*RESIZE_FACTOR, img.shape[0]*RESIZE_FACTOR), interpolation=cv2.INTER_CUBIC)

        detection_more = orc(metadata, im_resized, times, ocr_num=2)
        match(metadata, PHI, detection_more, times, ocr_num=2)
        detection = pd.concat([detection_more, detection], ignore_index=True, sort=True)

      # Clean Image Pixels
      removals = pixel_deidentify(dicom, img_orig, im_resized, detection, times, ocr_num=0)
      calc_stats(removals)

      df = df.append(metadata)
      times_per_image.append(times)

      log.info('Finished Processing: %s' % filepath)
      # break

  save_stats()
  calc_timing_stats(times_per_image)
  log.info('DONE.')

except Exception as e:
  import traceback
  print(traceback.format_exc())
  from IPython import embed
  embed() # drop into an IPython session



