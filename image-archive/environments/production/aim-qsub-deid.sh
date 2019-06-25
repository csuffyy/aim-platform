#!/bin/bash
# Usage:
# INPUT_FILE_LIST=~/Disk1_Part_aa OUTPUT_THUMBNAIL_DIR=/hpf/largeprojects/diagimage_common/shared/thumbnails aim-qsub.sh

#PBS -l mem=8gb,vmem=8gb
#PBS -l nodes=1:ppn=1
#PBS -l walltime=24:00:00
#PBS -j oe
#PBS -o /hpf/largeprojects/diagimage_common/shared/logs/deid-all

set -x

source ~/aim-platform/image-archive/environments/production/deid-env.sh
export ELASTIC_IP='192.168.100.61' # special elastic location via tunnel when in HPF
export INPUT_FILE_LIST=/hpf/largeprojects/diagimage_common/shared/dicom-paths/Subset__shared_inventory_extraction_disk1__aa
export ELASTIC_INDEX='deid_image'
export ELASTIC_DOC_TYPE='deid_image'
export TESSDATA_PREFIX=/home/dsnider/tessdata
# TODO VARIABLE FOR PATH: double check path in aim-qsub.sh script ---> #PBS -o /home/dsnider/jobs

echo "ENV:"
env

module load python/3.7.1_GDCM
module load tesseract/4.0.0

cd ~/aim-platform/image-archive/de-id/ # important (some paths are not absolute :-())
python ~/aim-platform/image-archive/de-id/deid_dicoms.py \
  --input_filelist $INPUT_FILE_LIST \
  --input_base_path "/hpf/largeprojects/diagimage_common/" \
  --input_report_base_path "/hpf/largeprojects/diagimage_common/shared/reports/" \
  --output_folder "/hpf/largeprojects/diagimage_common/shared/deid-all/" \
  --output_folder_suffix "" \
  --deid_recipe "/home/dsnider/aim-platform/image-archive/de-id/deid.recipe" \
  --gifs \
  --overwrite_report \
  --timeout 300