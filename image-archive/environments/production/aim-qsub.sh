#!/bin/bash
# Usage:
# INPUT_FILE_LIST=~/Disk1_Part_aa OUTPUT_THUMBNAIL_DIR=/hpf/largeprojects/diagimage_common/shared/thumbnails aim-qsub.sh

#PBS -l mem=8gb,vmem=8gb
#PBS -l nodes=1:ppn=1
#PBS -l walltime=00:40:00
#PBS -j oe
#PBS -o /home/chuynh/kiddata/jobs

export CPU=1
export RAM=8

module load python/3.7.1_GDCM

ES_BLUK_INSERT_SIZE = 500

python /home/chuynh/aim-platform/image-archive/de-id/load_elastic.py $INPUT_FILE_LIST $OUTPUT_THUMBNAIL_DIR -n $ES_BLUK_INSERT_SIZE
