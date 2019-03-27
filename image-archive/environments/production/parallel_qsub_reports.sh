mv jobs/* jobs-old

sed -i 's/export INPUT_FILE_LIST.*/export INPUT_FILE_LIST\=~\/Disk1_Part_aa/g' ./aim-platform/image-archive/environments/production/aim-qsub-reports.sh
qsub ./aim-platform/image-archive/environments/production/aim-qsub-reports.sh
