import random
import pydicom
import datetime

def dicom_to_dict(dicom, log=None, environ=None):
  dicom_metadata = {}
  [dicom_metadata.__setitem__(key,str(dicom.get(key))) for key in dicom.dir() if key not in ['PixelData']]

  for key, value in dicom_metadata.items():
    from IPython import embed
    embed() # drop into an IPython session

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

  if 'TransferSyntaxUID' not in dicom.file_meta:
    # Guess a transfer syntax if none is available
    dicom.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian  # 1.2.840.10008.1.2
    dicom.add_new(0x19100e, 'FD', [0,1,0]) # I have no idea what this last vector should actually be
    dicom[0x19100e].value = 'Assumed TransferSyntaxUID'
    if log: log.warning('Assumed TransferSyntaxUID')
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

  # PatientAgeInt (Method 1: diff between birth and acquisition dates)
  try:
    if 'PatientBirthDate' in dicom_metadata and 'AcquisitionDate' in dicom_metadata:
      PatientBirthDate = datetime.strptime(dicom_metadata['PatientBirthDate'], '%Y%m%d')
      AcquisitionDate = datetime.strptime(dicom_metadata['AcquisitionDate'], '%Y%m%d')
    age = AcquisitionDate - PatientBirthDate
    age = int(age.days / 365) # age in years
    dicom_metadata['PatientAgeInt'] = age
  except:
    if log: log.warning('Falling back for PatientAge')
  # PatientAgeInt (Method 2: str to int)
  try:
    if 'PatientAge' in dicom_metadata:
      age = dicom_metadata['PatientAge'] # usually looks like '06Y'
      if 'Y' in age:
        age = age.split('Y')
        age = int(age[0])
        dicom_metadata['PatientAgeInt'] = age
  except:
    if log: log.warning('Didn\'t understand value: %s = \'%s\'' % ('PatientAge', dicom_metadata['PatientAge']))
  if environ and environ=='local':
    if 'PatientAgeInt' not in dicom_metadata:
      # DEMO ONLY!!!! Add random age
      dicom_metadata['PatientAgeInt'] = random.randint(1,18)
    if 'PatientSex' not in dicom_metadata:
      dicom_metadata['PatientSex'] = 'Male' if random.randint(0,1) else 'Female'

  return dicom_metadata