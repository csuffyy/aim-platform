#!/bin/bash

#PBS -l mem=1gb,vmem=1gb
#PBS -l nodes=1:ppn=1
#PBS -l walltime=99:99:99
#PBS -j oe
#PBS -o /home/dsnider/jobs

while read FILE; do
  IFS='/' read -a ARRAY <<< "$FILE"
  NEWPATH=''
  for INDEX in "${!ARRAY[@]}"
  do
    if [ "$INDEX" -eq "5" ]; then
      NEWPATH="$NEWPATH/shared/deid-all"
    fi
    NEWPATH="$NEWPATH/${ARRAY[INDEX]}"
  done
  if [ -f $NEWPATH ]; then
    continue
  fi
  mkdir -p $(dirname $NEWPATH)
  # retVal=$?
  # if [ $retVal -ne 0 ]; then
  #   df
  #   df -h
  #   echo "Error"
  #   echo "$FILE"
  #   echo "$NEWPATH"
  #   echo -e "\n"
  #   continue
  # fi
  cp $FILE $NEWPATH
done </hpf/largeprojects/diagimage_common/shared/dicom-paths/Subset__src_disk3__aw