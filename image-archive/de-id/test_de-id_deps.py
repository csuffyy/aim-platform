
import os
import re
import cv2
import time
import glob
import random
import pickle
import logging
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
from shutil import copyfile
from elasticsearch import Elasticsearch

import pydicom
from matplotlib import pyplot as plt
filename = "../images/sample-dicom/OT-MONO2-8-hip.dcm"
ds = pydicom.dcmread(filename, force=True)
ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian  # 1.2.840.10008.1.2
data = ds.pixel_array
plt.imshow(data, cmap='gray')
plt.show()
plt.savefig('testplot.png')
os.remove('testplot.png')
