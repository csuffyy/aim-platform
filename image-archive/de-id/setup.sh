#!/bin/bash
set -x
set -e

sudo apt-get install -y python3-tk # for matplotlib
sudo apt-get install -y python3.7-dev libpython3.7-dev python3-pip
# sudo pip3 install virtualenv
# virtualenv -p python3.7 venv
# cd venv/
# . bin/activate
pip3 install numpy IPython scikit-image matplotlib pandas Pillow click pydicom pytesseract opencv-python python-Levenshtein fuzzywuzzy elasticsearch dateparser

# Install GDCM
sudo apt-get install python-gdcm # for pydicom
git clone --branch master https://github.com/HealthplusAI/python3-gdcm.git && cd python3-gdcm && dpkg -i build_1-1_amd64.deb && apt-get install -f
sudo cp /usr/local/lib/gdcm.py /usr/local/lib/python3.7/dist-packages/
sudo cp /usr/local/lib/gdcmswig.py /usr/local/lib/python3.7/dist-packages/
sudo cp /usr/local/lib/_gdcmswig.so /usr/local/lib/python3.7/dist-packages/
sudo cp /usr/local/lib/libgdcm* /usr/local/lib/python3.7/dist-packages/

# cp /usr/local/lib/gdcm.py ./lib/python3.7/site-packages/
# cp /usr/local/lib/gdcmswig.py ./lib/python3.7/site-packages/
# cp /usr/local/lib/_gdcmswig.so ./lib/python3.7/site-packages/
# cp /usr/local/lib/libgdcm* ./lib/python3.7/site-packages/


