#!/bin/bash
#
# Description: Extract and list files
#
# Usage:
# qsub -v INPUT_PATH="src/disk1" ~/qsub-find-dicom.sh
#
# Output:
# ls /hpf/largeprojects/diagimage_common/shared/dicom-paths

#PBS -l mem=512mb,vmem=512mb
#PBS -l nodes=1:ppn=1
#PBS -l walltime=99:00:00
#PBS -j oe
#PBS -o /home/dsnider/jobs/find_reports

set -x

INPUT_PATH="$INPUT_PATH"
BASE_PATH="/hpf/largeprojects/diagimage_common/"
OUTPUT_PATH="/hpf/largeprojects/diagimage_common/shared/dicom-paths/"
OUTPUT_FILENAME=$(echo $INPUT_PATH | sed 's/\//_/g')

env
echo -e "\n\n"

find "$BASE_PATH/$INPUT_PATH/" | grep dcm > "$OUTPUT_PATH/File_List__$OUTPUT_FILENAME.txt"

echo -e "Done."
