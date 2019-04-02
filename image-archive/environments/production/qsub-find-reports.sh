#!/bin/bash
#
# Description: Extract and list files
#
# Usage:
# qsub -v INPUT_FILE="BloorView_report.zip" ~/qsub-find-reports.sh
#
# Output:
# ls /hpf/largeprojects/diagimage_common/shared/reports

#PBS -l mem=512mb,vmem=512mb
#PBS -l nodes=1:ppn=1
#PBS -l walltime=72:00:00
#PBS -j oe
#PBS -o /home/dsnider/jobs/find_reports

set -x

INPUT_FILE="$INPUT_FILE"
INPUT_PATH="/hpf/largeprojects/diagimage_common/src/disk3/PACS_reports/"
OUTPUT_PATH="/hpf/largeprojects/diagimage_common/shared/reports/"
env

echo -e "\n\n"

mkdir "$OUTPUT_PATH/$INPUT_FILE/"
unzip -o "$INPUT_PATH/$INPUT_FILE" -d "$OUTPUT_PATH/$INPUT_FILE/"
find "$OUTPUT_PATH/$INPUT_FILE/" | grep txt > "$OUTPUT_PATH/File_List__$INPUT_FILE.txt"

echo -e "Done."
