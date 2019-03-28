#!/bin/bash

echo "THIS FILE IS DEPRECATED. It doesn't obtain all documents because it doesn't use elasticsearch scrolling. See elastic_dumpp_field.py"

HOST_IP="${HOST_IP:-localhost}"
ELASTIC_PORT="${ELASTIC_PORT:-9200}"
ELASTIC_INDEX="${ELASTIC_INDEX:-report}"
ELASTIC_DOC_TYPE="${ELASTIC_DOC_TYPE:-report}"

FIELD="${FIELD:-Report}"
OUTPUT_FILE="${OUTPUT_FILE:-elastic_dump_field.json}"


NUM_HITS=$(curl -H 'Content-Type: application/json' -XGET http://$HOST_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_search -d '
{
    "_source":["$FIELD"],
    "from" : 0,
    "size" : "1"
}' | jq .hits.total)


ITER_RATE=1000 # request this many records from elastic on each HTTP call
for((i=0;i<=$NUM_HITS;++i)) do
    curl -H 'Content-Type: application/json' -XGET http://$HOST_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_search -d "
    {
        \"_source\":[\"$FIELD\"],
        \"from\" : $i,
        \"size\" : $ITER_RATE
    }" |  jq ".hits.hits[] | {id: ._id, report: ._source.$FIELD}" >> $OUTPUT_FILE
done


# Put commas where needed: after every } --> }, Makes for valid json.
sed -i -e 's/}/},/g' $OUTPUT_FILE
# Enclose document in []
sed -i '1s/^/[/' $OUTPUT_FILE # add '[' to start of file
sed -i '$ s/.$/]/' $OUTPUT_FILE # replace , at end of file with ]