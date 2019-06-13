#!/bin/bash
#set -x
BASE_PATH="/hpf/largeprojects/diagimage_common/shared/dicom-paths"
NUM_JOBS_TOTAL=$(ls $BASE_PATH | grep Subset | wc -l)
COUNT=0
for FILENAME in $BASE_PATH/Subset_*; do
  sed -i 's,/hpf/largeprojects/diagimage_common/shared/dicom-paths/.*,/hpf/largeprojects/diagimage_common/shared/dicom-paths/'"$FILENAME"',g' ./aim-platform/image-archive/environments/production/qsub-copy-dicoms.sh
  qsub ./aim-platform/image-archive/environments/production/qsub-copy-dicoms.sh
  COUNT=$((COUNT+1))
  echo "Submitted Job $COUNT of $NUM_JOBS_TOTAL. Processing file: $FILENAME"
  sleep 0.05
  break
done
