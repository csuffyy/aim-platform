
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

cat /hpf/largeprojects/diagimage_common/src/disk1 | grep -i '\.dcm' > ~/Disk1_FileList_DCM.txt &
cat /hpf/largeprojects/diagimage_common/src/disk2 | grep -i '\.dcm' > ~/Disk2_FileList_DCM.txt &
cat /hpf/largeprojects/diagimage_common/src/disk3 | grep -i '\.dcm' > ~/Disk3_FileList_DCM.txt &
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
## Find all Dicoms
##
qsub -v INPUT_PATH="shared/inventory/extraction/disk1/" -N dicom_extraction_disk1 ~/qsub-find-dicom.sh
qsub -v INPUT_PATH="shared/inventory/extraction/disk2/" -N dicom_extraction_disk2 ~/qsub-find-dicom.sh
qsub -v INPUT_PATH="shared/inventory/extraction/disk3/" -N dicom_extraction_disk3 ~/qsub-find-dicom.sh
qsub -v INPUT_PATH="src/disk1/" -N dicom_src_disk1 ~/qsub-find-dicom.sh
qsub -v INPUT_PATH="src/disk2/" -N dicom_src_disk2 ~/qsub-find-dicom.sh
qsub -v INPUT_PATH="src/disk3/" -N dicom_src_disk3 ~/qsub-find-dicom.sh

##
## REPORTS
##
sed -e 's/^/\/hpf\/largeprojects\/diagimage_common\/src\/disk3\/PACS_reports\/reports_A\//' -i ~/reports_A_filelist # prefix text infront of each line in file if you need to 
./aim-platform/image-archive/environments/production/aim-qsub-reports.sh
qsub ./aim-platform/image-archive/environments/production/aim-qsub-reports.sh

# Find All Reports
qsub -v INPUT_FILE="BloorView_report.zip" -N report_BloorView_report ~/qsub-find-reports.sh 
qsub -v INPUT_FILE="HSC_report_0_500K.zip" -N report_HSC_report_0_500K ~/qsub-find-reports.sh 
qsub -v INPUT_FILE="HSC_report_1.5M_2M.zip" -N report_HSC_report_1.5M_2M ~/qsub-find-reports.sh 
qsub -v INPUT_FILE="HSC_report_1M_1.5M.zip" -N report_HSC_report_1M_1.5M ~/qsub-find-reports.sh 
qsub -v INPUT_FILE="HSC_report_2.5M_3M.zip" -N report_HSC_report_2.5M_3M ~/qsub-find-reports.sh 
qsub -v INPUT_FILE="HSC_report_2M_2.5M.zip" -N report_HSC_report_2M_2.5M ~/qsub-find-reports.sh 
qsub -v INPUT_FILE="HSC_report_500K_1M.zip" -N report_HSC_report_500K_1M ~/qsub-find-reports.sh 


wc -l /hpf/largeprojects/diagimage_common/shared/dicom-paths/*.txt
wc -l /hpf/largeprojects/diagimage_common/shared/reports/*.txt


32075764 /hpf/largeprojects/diagimage_common/shared/dicom-paths/File_List__shared_inventory_extraction_disk1_.txt
31256545 /hpf/largeprojects/diagimage_common/shared/dicom-paths/File_List__shared_inventory_extraction_disk2_.txt
30552510 /hpf/largeprojects/diagimage_common/shared/dicom-paths/File_List__shared_inventory_extraction_disk3_.txt
      1 /hpf/largeprojects/diagimage_common/shared/dicom-paths/File_List__shared_test_.txt
1481364 /hpf/largeprojects/diagimage_common/shared/dicom-paths/File_List__src_disk1_.txt
1408525 /hpf/largeprojects/diagimage_common/shared/dicom-paths/File_List__src_disk2_.txt
2245071 /hpf/largeprojects/diagimage_common/shared/dicom-paths/File_List__src_disk3_.txt
99,019,780 total

   6943 /hpf/largeprojects/diagimage_common/shared/reports/File_List__BloorView_report.zip.txt
 408767 /hpf/largeprojects/diagimage_common/shared/reports/File_List__HSC_report_0_500K.zip.txt
 369386 /hpf/largeprojects/diagimage_common/shared/reports/File_List__HSC_report_1.5M_2M.zip.txt
 384889 /hpf/largeprojects/diagimage_common/shared/reports/File_List__HSC_report_1M_1.5M.zip.txt
 239191 /hpf/largeprojects/diagimage_common/shared/reports/File_List__HSC_report_2.5M_3M.zip.txt
 358444 /hpf/largeprojects/diagimage_common/shared/reports/File_List__HSC_report_2M_2.5M.zip.txt
 407171 /hpf/largeprojects/diagimage_common/shared/reports/File_List__HSC_report_500K_1M.zip.txt
2,174,791 total

# Rerun disk1 extraction with 99h walltime
[dsnider@qlogin3 ~]$ qsub -v INPUT_PATH="shared/inventory/extraction/disk1/" -N dicom_extraction_disk1 ~/qsub-find-dicom.sh
46870171




