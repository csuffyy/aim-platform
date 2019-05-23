default_iface=$(awk '$2 == 00000000 { print $1 }' /proc/net/route)
IP=$(ip addr show dev "$default_iface" | awk '$1 == "inet" { sub("/.*", "", $2); print $2 }')
export ENVIRON="local"
export PUBLIC_IP="$IP"
export ELASTIC_IP="$IP"
export FALLBACK_ELASTIC_IP="$IP"
export FALLBACK_ELASTIC_PORT=9200
export ELASTIC_PORT=9200
export ELASTIC_INDEX="image"
export ELASTIC_DOC_TYPE="image"
export LINKING_ELASTIC_INDEX="linking"
export LINKING_ELASTIC_DOC_TYPE="linking"
export ELASTIC_URL="http://$IP:9200/"
export REPORT_ELASTIC_INDEX="report"
export REPORT_ELASTIC_DOC_TYPE="report"
export FILESERVER_IP="$IP"
export FILESERVER_PORT="3000"
export FILESERVER_DICOM_PATH="/home/dan/aim-platform/image-archive/reactive-search/"
export FILESERVER_THUMBNAIL_PATH="static/thumbnails"
export AUTH_TOKEN="771100"
export FILESERVER_TOKEN=""
export STATIC_WEBSERVER_URL="http://$IP:3000/"
export DWV_URL="http://$IP:8080/"
