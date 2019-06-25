#!/bin/bash
# Usage:
# INPUT_FILE_LIST=~/Disk1_Part_aa OUTPUT_THUMBNAIL_DIR=/hpf/largeprojects/diagimage_common/shared/thumbnails aim-qsub.sh

#PBS -l mem=4gb,vmem=4gb
#PBS -l nodes=1:ppn=1
#PBS -l walltime=24:00:00
#PBS -j oe
#PBS -o /hpf/largeprojects/diagimage_common/shared/logs

set -x

source aim-platform/image-archive/environments/production/env.sh
export ELASTIC_IP='192.168.100.61' # special elastic location via tunnel when in HPF
export FILESERVER_TOKEN='-0TO0-224400'
export INPUT_FILE_LIST=/hpf/largeprojects/diagimage_common/shared/dicom-paths/Subset__shared_inventory_extraction_disk1__aa
export OUTPUT_THUMBNAIL_DIR=/hpf/largeprojects/diagimage_common/shared/thumbnails
export ELASTIC_INDEX='deid_image'
export ELASTIC_DOC_TYPE='deid_image'
# TODO VARIABLE FOR PATH: double check path in aim-qsub.sh script ---> #PBS -o /home/dsnider/jobs

echo "ENV:"
env

module load python/3.7.1_GDCM

python /home/dsnider/aim-platform/image-archive/de-id/load_elastic.py $INPUT_FILE_LIST $OUTPUT_THUMBNAIL_DIR -n $ES_BLUK_INSERT_SIZE
