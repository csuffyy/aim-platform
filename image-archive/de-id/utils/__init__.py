import random
import pydicom
import datetime

def dicom_to_dict(dicom, log=None, environ=None):
  dicom_metadata = {}
  [dicom_metadata.__setitem__(key,str(dicom.get(key))) for key in dicom.dir() if key not in ['PixelData']]

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
    # Remove bytes datatype from metadata because it can't be serialized for sending to elasticsearch
    if type(dicom_metadata[key]) is bytes:
      dicom_metadata.pop(key, None) # remove

    if log: log.debug('%s: %s' % (key, value))

  # PatientBirthDatePretty
  try:
    if 'PatientBirthDate' in dicom_metadata:
      PatientBirthDate = datetime.strptime(dicom_metadata['PatientBirthDate'], '%Y%m%d')
      dicom_metadata['PatientBirthDatePretty'] = datetime.strftime(PatientBirthDate,'%Y-%m-%d')
      datetime.strptime(dicom_metadata['PatientBirthDatePretty'], '%Y-%m-%d')  # just check that it works
  except:
    if log: log.warning('Didn\'t understand value: %s = \'%s\'' % ('PatientBirthDate', dicom_metadata['PatientBirthDate']))
    dicom_metadata.pop('PatientBirthDatePretty', None) # remove bad formatted metadata
  # AcquisitionDatePretty
  try:
    if 'AcquisitionDate' in dicom_metadata:
      AcquisitionDate = datetime.strptime(dicom_metadata['AcquisitionDate'], '%Y%m%d')
      dicom_metadata['AcquisitionDatePretty'] = datetime.strftime(AcquisitionDate,'%Y-%m-%d')
      datetime.strptime(dicom_metadata['AcquisitionDatePretty'], '%Y-%m-%d')  # just check that it works
  except:
    if log: log.warning('Didn\'t understand value: %s = \'%s\'' % ('AcquisitionDate', dicom_metadata['AcquisitionDate']))
    dicom_metadata.pop('AcquisitionDatePretty', None) # remove bad formatted metadata

  # # Convert any values that can be displayed as a string (things that need to be numbers should follow this)
  # for k, v in dicom_metadata.items():
  #   # convert to string if not already a string and has str method
  #   if not isinstance(v,str) and '__str__' in dir(v):
  #     dicom_metadata[k] = dicom_metadata[key].__str__()

  return dicom_metadata