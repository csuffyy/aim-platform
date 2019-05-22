#!/bin/bash

# Get code
qlogin
cd ~/aim-platform/image-archive
git pull

# Create Elastic index to store de-id mappings
source ./environments/local/env.sh
source ./environments/production/env.sh
export ELASTIC_IP='192.168.100.61' # special elastic location via tunnel when in HPF
export LINKING_ELASTIC_INDEX=linking-anna-alex-abhi-2
export LINKING_ELASTIC_DOC_TYPE=linking-anna-alex-abhi-2
./elastic-search/init_elastic.sh

# Make output path
cd ~/aim-platform/image-archive
OUTPUT_PATH="/hpf/largeprojects/diagimage_common/shared/deid/$LINKING_ELASTIC_INDEX"
mkdir -p $OUTPUT_PATH

# Download list of DICOM files
  # --input=$ELASTIC_IP:$ELASTIC_PORT \
elasticdump \
  --input=https://elasticimages.ccm.sickkids.ca \
  --output=$ \
  --headers='{"X-Requested-With": "224400"}' \
  --searchBody='{"query":{"bool":{"must":[{"bool":{"must":[{"query_string":{"query":"Rows:/1[3-9][0-9][0-9]/ AND Columns:512 AND Body AND NOT SeriesNumber:999* AND NOT SAGITTAL AND Modality:MR"}},{"range":{"PatientAgeInt":{"gte":0,"lte":30,"boost":2}}}]}}]}}}' \
| jq ._source.dicom_filepath | tee list_of_dicom_paths.txt

# Split list of dicoms into smaller amounts (to be run in parallel)
split -l 100 list_of_dicom_paths.txt Subset_list_of_dicom_paths_

# Create and submit de-id job qsub script
NUM_JOBS_TOTAL=$(ls ~/Subset* | wc -l)
COUNT=0
for FILENAME in ~/Subset_*; do
  # echo $FILENAME
# done
  cat <<EOT > qsub-deid-temp.sh
#!/bin/bash

#PBS -l mem=16gb,vmem=16gb
#PBS -l nodes=1:ppn=2
#PBS -l walltime=100:00:00
#PBS -j oe
#PBS -o /home/dsnider/jobs

set -x

source ~/aim-platform/image-archive/environments/production/env.sh
export ELASTIC_IP='192.168.100.61' # special elastic location via tunnel when in HPF
export LINKING_ELASTIC_INDEX=linking-anna-alex-abhi-2
export LINKING_ELASTIC_DOC_TYPE=linking-anna-alex-abhi-2

module load python/3.7.1_GDCM

python3.7 ~/aim-platform/image-archive/de-id/deid_dicoms.py --input_files $FILENAME --output_folder $OUTPUT_PATH --deid_recipe ~/aim-platform/image-archive/de-id/deid.dicom --no_pixel
EOT
  qsub qsub-deid-temp.sh
  COUNT=$((COUNT+1))
  echo "Submitted Job $COUNT of $NUM_JOBS_TOTAL. Processing file: $FILENAME"
  sleep 0.05
done


