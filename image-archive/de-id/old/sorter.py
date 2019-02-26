import os
import pydicom

from shutil import copyfile

import logging
logging.basicConfig(format='%(asctime)s.%(msecs)d[%(levelname)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)
log = logging.getLogger('main')
log.info('Starting Pixel De-Identify')

input_folder = '/home/dan/Two_Images'
output_folder_base = '/home/dan/output'

for subdir, dirs, files in os.walk(input_folder):
  for filename in files:
    filepath =  os.path.join(subdir, filename)

    # Load Image
    dicom = pydicom.dcmread(filepath, force=True)
    if 'Modality' in dicom:
      modality = dicom.Modality
    else:
      modality = 'NONE'

    # Copy to a folder based on modality
    output_folder =  os.path.join(output_folder_base, modality)
    output_file =  os.path.join(output_folder_base, modality, filename)
    if not os.path.exists(output_folder):
      os.makedirs(output_folder)
    copyfile(filepath, output_file)
    log.info('Saved to: %s' % output_file)

log.info('\nFinished.\n')