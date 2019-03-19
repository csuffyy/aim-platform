
# This guide assumes elastic and 172.20.4.83:3000 is runnig on your AIM-server

# AIM Tunnel to get a static file webserver on port 8000 out of HPF through port 22 to Openstack port 8000
# Run tunnel on data1.ccm.sickkids.ca
ssh -fNq -R 0.0.0.0:8000:localhost:8000 ubuntu@172.20.4.83
# Run webserver on data1.ccm.sickkids.ca
cd /hpf/largeprojects/diagimage_common
# python aim-platform/image-archive/environments/hpf/static_webserver.py
export TOKEN='771100'
python ~/hpf_static_server.py
# Test from AIM-server
curl 172.20.4.83:8000/src/disk1/Images/NASLibrary10/2000/02/09/1559937/75473475.dcm-0TO0-771100.dcm
curl 172.20.4.83:8000/shared/thumbnails/test.png-0TO0-771100

# AIM tunnel elasticsearch running on OpenStack VM (port 9200) to HPF data server (port 9200)
# Run on hpf23.ccm.sickkids.ca
ssh -fNq -L 0.0.0.0:9200:localhost:9200 ubuntu@172.20.4.83
ip a
curl 192.168.100.61:9200
qlogin -l nodes=qlogin1.hpf.new
curl 192.168.100.61:9200
qlogin -l nodes=qlogin11.ccm.sickkids.ca
curl 192.168.100.61:9200

# List DCM files to upload to HPF
# Run on hpf23.ccm.sickkids.ca
cd TO_FOLDER_YOU_WANT_TO_LOAD
find "$(pwd)" -iname "*.dcm" > list_of_dicoms.txt # find all DCMs and print full path
sed -e 's/^/\/hpf\/largeprojects\/diagimage_common\/src\//' -i Disk1_FileList_DCM.txt # prefix text infront of each line in file if you need to 
split -l 50000 Disk1_FileList_DCM.txt  Disk1_Part_ # split list of files into smaller groups of 50000 line

# Submit a qjob
# Run on hpf23.ccm.sickkids.ca
source aim-platform/image-archive/environments/production/env.sh
export ELASTIC_IP='192.168.100.61' # special elastic location via tunnel when in HPF
export FALLBACK_ELASTIC_IP='192.168.100.61' # special elastic location via tunnel when in HPF
export FILESERVER_TOKEN='-0TO0-771100'
export INPUT_FILE_LIST=~/Disk1_Part_aa
export OUTPUT_THUMBNAIL_DIR=/hpf/largeprojects/diagimage_common/shared/thumbnails
# double check path in aim-qsub.sh script ---> #PBS -o /home/dsnider/jobs
qsub ./aim-platform/image-archive/environments/production/aim-qsub.sh

# Confirm everything is working
1. Open 172.20.4.83:3000
2. Find a newly added entry
3. Check that thumbnail works
4. Check that DCM viewer works
