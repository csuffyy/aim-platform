
## Dependencies

```
sudo apt-get install python3-tk # for matplotlib
sudo apt-get install gdcm openjpeg2 # for pydicom
sudo apt-get install python3.7-dev libpython3.7-dev
virtualenv -p python3.7 python3.7venv
cd python3.7venv/
. bin/activate
pip3.7 install numpy IPython scikit-image matplotlib pandas Pillow click pydicom pytesseract opencv-python python-Levenshtein fuzzywuzzy elasticsearch
git clone --branch master https://github.com/HealthplusAI/python3-gdcm.git && cd python3-gdcm && dpkg -i build_1-1_amd64.deb && apt-get install -f
cp /usr/local/lib/gdcm.py ./lib/python3.7/site-packages/
cp /usr/local/lib/gdcmswig.py ./lib/python3.7/site-packages/
cp /usr/local/lib/_gdcmswig.so ./lib/python3.7/site-packages/
cp /usr/local/lib/libgdcm* ./lib/python3.7/site-packages/
```
