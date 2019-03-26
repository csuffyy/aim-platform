#!/bin/bash

# Run on Data
nohup find /hpf/largeprojects/diagimage_common/src/disk1 > ~/Disk1_FileList_ALL.txt &
nohup find /hpf/largeprojects/diagimage_common/src/disk2 > ~/Disk2_FileList_ALL.txt &
nohup find /hpf/largeprojects/diagimage_common/src/disk3 > ~/Disk3_FileList_ALL.txt &
nohup find /hpf/largeprojects/diagimage_common/shared/inventory/extraction/ > ~/Extraction_FileList_ALL.txt &

# Monitor
while true; do tail ~/Disk1_FileList_ALL.txt; echo ""; ps -ef | grep find; date; sleep 5; done
while true; do tail ~/Disk2_FileList_ALL.txt; echo ""; ps -ef | grep find; date; sleep 5; done
while true; do tail ~/Disk3_FileList_ALL.txt; echo ""; ps -ef | grep find; date; sleep 5; done
while true; do tail ~/Extraction_FileList_ALL.txt; echo ""; ps -ef | grep find; date; sleep 5; done
