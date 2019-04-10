#!/bin/bash

#PBS -l mem=1gb,vmem=1gb
#PBS -l nodes=1:ppn=2
#PBS -l walltime=100:00:00
#PBS -j oe
#PBS -o /home/dsnider/jobs

set -x

source aim-platform/image-archive/environments/production/env.sh
export ES_BLUK_INSERT_SIZE=50
export ELASTIC_IP='192.168.100.61' # special elastic location via tunnel when in HPF
export FALLBACK_ELASTIC_IP='192.168.100.61' # special elastic location via tunnel when in HPF
export INPUT_FILE_LIST=~/reports_A_filelist_SHORT
# TODO VARIABLE FOR PATH: double check path in aim-qsub.sh script ---> #PBS -o /home/dsnider/jobs

echo "ENV:"
env

module load python/3.7.1_GDCM

python /home/dsnider/aim-platform/image-archive/de-id/load_reports_elastic.py $INPUT_FILE_LIST -n $ES_BLUK_INSERT_SIZE
