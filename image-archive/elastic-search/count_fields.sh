for FIELD_NAME in $(curl -s -XGET localhost:9200/image/_mapping | jq .image.mappings.image.properties | jq 'keys' | jq .[]); do FIELD_NAME=$(echo "$FIELD_NAME" | tr -d '"') ;  NUM_NOT_NULL=$(curl -s -X POST "localhost:9200/image/_search?size=0" -H 'Content-Type: application/json' -d'
{
    "aggs" : {
        "types_count" : { "value_count" : { "field" : "'$FIELD_NAME'.keyword" } }
    }
}
' | jq .aggregations.types_count.value);   echo "$NUM_NOT_NULL"; done > out 

paste -sd+ out | bc
