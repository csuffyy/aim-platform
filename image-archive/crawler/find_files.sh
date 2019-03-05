#!/bin/bash

nohup find disk1 > ~/Disk1_FileList_ALL.txt &

# Monitor
while true; do tail ~/Disk1_FileList_ALL.txt; echo ""; ps -ef | grep find; date; sleep 5; done
