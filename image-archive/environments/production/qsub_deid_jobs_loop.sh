#!/bin/bash
#set -x
BASE_PATH="/home/dsnider/SubsetStationName"
NUM_JOBS_TOTAL=$(ls $BASE_PATH | grep Subset | wc -l)
COUNT=0
for FILENAME in $BASE_PATH/Subset_*; do
  sed -i 's,export INPUT_FILE_LIST.*,export INPUT_FILE_LIST\='"$FILENAME"',g' ./aim-platform/image-archive/environments/production/aim-qsub-deid.sh
  qsub ./aim-platform/image-archive/environments/production/aim-qsub-deid.sh
  COUNT=$((COUNT+1))
  echo "Submitted Job $COUNT of $NUM_JOBS_TOTAL. Processing file: $FILENAME"
  sleep 0.05
done
