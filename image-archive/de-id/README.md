
## Dependencies

```
# pip2.7 install numpy mahotas IPython==5.8.0 scikit-image matplotlib==2.2.3 scipy pandas Pillow click pydicom==1.1.0 pytesseract opencv-python python-Levenshtein fuzzywuzzy
#sudo apt-get install python-tk # for matplotlib



pip uninstall pydicom
pip install pydicom==1.1.0
sudo apt-get install python3-tk # for matplotlib
sudo apt-get install gdcm openjpeg2 # for pydicom



sudo apt-get install python3.7-dev libpython3.7-dev
virtualenv -p python3.7 python3.7venv
cd python3.7venv/
. bin/activate
pip3.7 install numpy mahotas IPython scikit-image matplotlib scipy pandas Pillow click pydicom pytesseract opencv-python python-Levenshtein fuzzywuzzy
git clone --branch master https://github.com/HealthplusAI/python3-gdcm.git && cd python3-gdcm && dpkg -i build_1-1_amd64.deb && apt-get install -f
cp /usr/local/lib/gdcm.py ./lib/python3.7/site-packages/
cp /usr/local/lib/gdcmswig.py ./lib/python3.7/site-packages/
cp /usr/local/lib/_gdcmswig.so ./lib/python3.7/site-packages/
cp /usr/local/lib/libgdcm* ./lib/python3.7/site-packages/
```



```
import pydicom
from matplotlib import pyplot as plt
filename = "94862596.dcm"
ds = pydicom.dcmread(filename)
data = ds.pixel_array
plt.imshow(data, cmap='gray')
plt.show()
```

sudo apt-get install python3.7-dev libpython3.7-dev virtualenv
sudo apt-get install python3-tk # for matplotlib
sudo apt-get install gdcm openjpeg2 # for pydicom
virtualenv -p python3.7 python3.7venv
cd python3.7venv/
. bin/activate
pip3.7 install numpy pydicom
git clone --branch master https://github.com/HealthplusAI/python3-gdcm.git && cd python3-gdcm && dpkg -i build_1-1_amd64.deb && apt-get install -f
cp /usr/local/lib/gdcm.py ./lib/python3.7/site-packages/
cp /usr/local/lib/gdcmswig.py ./lib/python3.7/site-packages/
cp /usr/local/lib/_gdcmswig.so ./lib/python3.7/site-packages/
cp /usr/local/lib/libgdcm* ./lib/python3.7/site-packages/
```



```
import pydicom
from matplotlib import pyplot as plt
filename = "94862596.dcm"
ds = pydicom.dcmread(filename)
data = ds.pixel_array
plt.imshow(data, cmap='gray')
plt.show()
```