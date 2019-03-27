
# This guide assumes elastic and 172.20.4.83:3000 is runnig on your AIM-server

# AIM Tunnel to get a static file webserver on port 8000 out of HPF through port 22 to Openstack port 8000
# Run tunnel on data1.ccm.sickkids.ca
ssh -fNq -R 0.0.0.0:8000:localhost:8000 ubuntu@172.20.4.83
# Run webserver on data1.ccm.sickkids.ca
# file from aim-platform/image-archive/environments/hpf/static_webserver.py
cd /hpf/largeprojects/diagimage_common
export TOKEN='771100'
nohup python ~/hpf_static_server.py &
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
nohup find /hpf/largeprojects/diagimage_common/src/disk1 > ~/Disk1_FileList_ALL.txt &
nohup find /hpf/largeprojects/diagimage_common/src/disk2 > ~/Disk2_FileList_ALL.txt &
nohup find /hpf/largeprojects/diagimage_common/src/disk3 > ~/Disk3_FileList_ALL.txt &
nohup find /hpf/largeprojects/diagimage_common/shared/inventory/extraction/ > ~/Extraction_FileList_ALL.txt &

cat ~/Disk1_FileList_ALL.txt | grep -i '\.dcm' > ~/Disk1_FileList_DCM.txt &
cat ~/Disk2_FileList_ALL.txt | grep -i '\.dcm' > ~/Disk2_FileList_DCM.txt &
cat ~/Disk3_FileList_ALL.txt | grep -i '\.dcm' > ~/Disk3_FileList_DCM.txt &
cat /hpf/largeprojects/diagimage_common/shared/inventory/extraction/ | grep -i '\.dcm' > ~/Extraction_FileList_DCM.txt &

# Monitor
while true; do tail ~/Disk1_FileList_ALL.txt; echo ""; ps -ef | grep find; date; sleep 5; done
while true; do tail ~/Disk2_FileList_ALL.txt; echo ""; ps -ef | grep find; date; sleep 5; done
while true; do tail ~/Disk3_FileList_ALL.txt; echo ""; ps -ef | grep find; date; sleep 5; done
while true; do tail ~/Extraction_FileList_ALL.txt; echo ""; ps -ef | grep find; date; sleep 5; done

# Split Files
cd TO_FOLDER_YOU_WANT_TO_LOAD
# find "$(pwd)" -iname "*.dcm" > list_of_dicoms.txt # find all DCMs and print full path
# sed -e 's/^/\/hpf\/largeprojects\/diagimage_common\/src\//' -i Disk1_FileList_DCM.txt # prefix text infront of each line in file if you need to 
split -l 50000 Disk1_FileList_DCM.txt  Disk1_Part_ # split list of files into smaller groups of 50000 line

# Submit a qjob
# Run on hpf23.ccm.sickkids.ca
sed -i 's/export INPUT_FILE_LIST.*/export INPUT_FILE_LIST\=~\/Disk1_Part_aa/g' ./aim-platform/image-archive/environments/production/aim-qsub.sh
qsub ./aim-platform/image-archive/environments/production/aim-qsub.sh

# Check log
alias qs="qstat -rn1 | grep dsni"
alias wqs="watch 'qstat -rn1 | grep dsni'"
function ql() {
    tail $1 -- "$(find jobs -maxdepth 1 -type f -printf '%T@.%p\0' | sort -znr -t. -k1,2 | while IFS= read -r -d '' -r record ; do printf '%s' "$record" | cut -d. -f3- ; break ; done)"
}
function qm() {
  tail -n100 jobs/aim-qsub.sh.o$(qstat -rn1 | grep dsnider | grep -v ' C '| cut -f1 -d' ' | tail -n1); qstat -rn1 | grep dsnider
}
function wqm() { # watch q-monitor
  while [ 1 ]; do cat jobs/aim-qsub.sh.o$(qstat -rn1 | grep dsnider | grep -v ' C '| cut -f1 -d' ' | tail -n1); qstat -rn1 | grep dsnider; sleep 1; test $? -gt 128 && break; done
}

# Confirm everything is working
1. Open 172.20.4.83:3000
2. Find a newly added entry
3. Check that thumbnail works
4. Check that DCM viewer works



##
## REPORTS
##

sed -e 's/^/\/hpf\/largeprojects\/diagimage_common\/src\/disk3\/PACS_reports\/reports_A\//' -i ~/reports_A_filelist # prefix text infront of each line in file if you need to