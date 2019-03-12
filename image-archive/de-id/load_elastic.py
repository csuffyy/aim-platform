#!/bin/python
# pip3 install elasticsearch
# docs: https://elasticsearch-py.readthedocs.io/en/master/
#
# Tips:
# curl -H 'Content-Type: application/json' -v http://192.168.136.128:9200/movieappfinal/_search?scroll=5m -d '{"query":{"match_all":{}}}' | jq
#
# TODO:
# - bulk elastic insert, instead of 1 by 1

import os
import cv2
import glob
import random
import pydicom
import logging
import traceback
import numpy as np

from IPython import embed
from shutil import copyfile
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch import helpers

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime

import matplotlib
from matplotlib import pyplot as plt
# matplotlib.use('TkAgg')

index_name = os.environ['ELASTIC_INDEX']
doc_type = os.environ['ELASTIC_DOC_TYPE']
input_folder = '../images/sample-dicom/' # TODO(Chris): Take path as parameter, so that it can be passed by subjobs.py
output_path = '../reactive-search/static/thumbnails/' # TODO(Chris): Take path as parameter, so that it can be passed by subjobs.py


logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
log = logging.getLogger('main')

es = Elasticsearch() # TODO(Daniel): Connect to remote elastic search

def save_thumbnail_of_dicom(dicom, filepath):
# def save_thumbnail_of_dicom(dicom, filepath, output_path): # TODO(Chris): Implement new parameter output_path, your home directory is OK.
  # if 'pixel_array' not in dicom:
  #   log.warning('Pixel data not found in DICOM: %s' % filepath)
  #   # copyfile(filepath, '%s_%s' % (output_path, filepath))
  #   return

  if 'TransferSyntaxUID' not in dicom.file_meta:
    dicom.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian  # 1.2.840.10008.1.2

  try:  
    img = dicom.pixel_array
  except Exception as e:
    print(traceback.format_exc())
    log.warning('Skipping this image because error occured when reading pixel_array')
    return

  # Image shape
  if img.shape == 0:
    log.warning('Image size is 0: %s' % filepath)
    # copyfile(filepath, '%s_%s' % (output_path, filepath))
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
    # TODO: Is there a more efficient way?
    image = Image.fromarray(img,'YCbCr')
    image = image.convert('RGB')
    img = np.array(image)
    # plt.imshow(img, cmap='gray')
    # plt.show()
    # More image modes: https://pillow.readthedocs.io/en/3.1.x/handbook/concepts.html#concept-modes
  if 'PhotometricInterpretation' in dicom and 'RGB' in dicom.PhotometricInterpretation:
    img = img[...,::-1]

  # # Convert to greyscale
  # if len(img.shape) == 3:
  #   img_orig = img
  #   image = Image.fromarray(img,'RGB')
  #   image = image.convert('L')
  #   img = np.array(image)
  # else:
  #   img_orig = img

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


  # try:
  # Colour image: 96677981.dcm, 88132678.dcm
  # Looks all white: 86512664.dcm
def load_images():
  for filepath in glob.iglob('%s/**/*.dcm' % input_folder, recursive=True):
    # Load Image
    dicom = pydicom.dcmread(filepath, force=True)
    dicom_metadata = {}
    [dicom_metadata.__setitem__(key,dicom.get(key)) for key in dicom.dir() if key not in ['PixelData']]

    log.info('\n\n\n%s' % filepath)
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
      # if key in ['RequestAttributesSequence', 'SequenceOfUltrasoundRegions', 'ProcedureCodeSequence', 'IconImageSequence', 'ReferencedPerformedProcedureStepSequence', 'ReferencedStudySequence', 'RequestedProcedureCodeSequence', 'RadiopharmaceuticalInformationSequence','ReferencedStudySequence', 'ReferencedStudySequence', 'DetectorInformationSequence', 'EnergyWindowInformationSequence', 'PatientGantryRelationshipCodeSequence', 'PatientOrientationCodeSequence', 'RadiopharmaceuticalInformationSequence','ReferencedStudySequence','RequestAttributesSequence', 'SourceImageSequence','CTExposureSequence','ProcedureCodeSequence','ReferencedImageSequence','ReferencedPatientSequence','ReferencedPerformedProcedureStepSequence','ReferencedStudySequence','RequestAttributesSequence','AnatomicRegionSequence']:
      if isinstance(dicom_metadata[key], list):
        if len(dicom_metadata[key])>0 and type(dicom_metadata[key][0]) is pydicom.dataset.Dataset:
          # Fix for error: TypeError("Unable to serialize 'ProcedureCodeSequence' (type: <class 'pydicom.dataset.Dataset'>)")")
          dicom_metadata[key] = dicom_metadata[key].__str__()

      log.info('%s: %s' % (key, value))

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
    if 'PatientAgeInt' not in dicom_metadata:
      dicom_metadata['PatientAgeInt'] = random.randint(1,20)

    # Remove bytes datatype from metadata because it can't be serialized for sending to elasticsearch
    filtered = {k: v for k, v in dicom_metadata.items() if type(v) is not bytes}
    dicom_metadata.clear()
    dicom_metadata.update(filtered)

    thumbnail_filepath = save_thumbnail_of_dicom(dicom, filepath)
    if not thumbnail_filepath:
      log.warning('Skipping this dicom. Could not generate thumbnail.')
      continue

    dicom_metadata['dicom_filepath'] = filepath
    dicom_metadata['dicom_filename'] = os.path.basename(filepath)
    # dicom_metadata['dicom_url'] = 'http://192.168.136.128:3000/static/dicom/%s' % os.path.basename(filepath)
    dicom_metadata['thumbnail_filepath'] = thumbnail_filepath
    dicom_metadata['thumbnail_filename'] = os.path.basename(thumbnail_filepath)
    dicom_metadata['original_title'] = 'Dicom'
    dicom_metadata['_index'] = index_name
    dicom_metadata['_type'] = doc_type
    yield dicom_metadata


def main():
  # Bulk load elastic
  res = helpers.bulk(es, load_images())
  log.info('Bulk insert result: %s, %s' % (res[0], res[1]))
  # Update Index
  es.indices.refresh(index=index_name)
  # Print Summary
  res = es.search(index=index_name, body={"query": {"match_all": {}}})
  log.info("Number of Search Hits: %d" % res['hits']['total'])
  # for hit in res['hits']['hits']:
  #     print("%(imdb_id)s %(original_title)s" % hit["_source"])
  log.info('Finished.')

main()

# except Exception as e:
#   import traceback
#   print(traceback.format_exc())
#   from IPython import embed
#   embed() # drop into an IPython session

