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
  mkdir -p $(dirname $NEWPATH)
  cp $FILE $NEWPATH
done </hpf/largeprojects/diagimage_common/shared/dicom-paths/Subset__src_disk3__ac