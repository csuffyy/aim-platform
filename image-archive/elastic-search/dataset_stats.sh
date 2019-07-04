Unique_Patient_MRNs=$(curl -s -H 'Content-Type: application/json' -XGET 'http://127.0.0.1:9200/image/image/_search' -d '
{
    "size" : 0,
    "aggs" : {
        "unique" : {
            "cardinality" : {
              "field" : "PatientID.keyword"
            }
        }
    }
}' | jq .aggregations.unique.value)
 

echo "Unique Patient MRNs: $(echo $Unique_Patient_MRNs | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')"




Unique_AccessionNumber=$(curl -s -H 'Content-Type: application/json' -XGET 'http://127.0.0.1:9200/image/image/_search' -d '
{
    "size" : 0,
    "aggs" : {
        "unique" : {
            "cardinality" : {
              "field" : "AccessionNumber.keyword"
            }
        }
    }
}' | jq .aggregations.unique.value)
 

echo "Unique AccessionNumber: $(echo $Unique_AccessionNumber | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')"




Unique_SeriesInstanceUID=$(curl -s -H 'Content-Type: application/json' -XGET 'http://127.0.0.1:9200/image/image/_search' -d '
{
    "size" : 0,
    "aggs" : {
        "unique" : {
            "cardinality" : {
              "field" : "SeriesInstanceUID.keyword"
            }
        }
    }
}' | jq .aggregations.unique.value)
 

echo "Unique SeriesInstanceUID: $(echo $Unique_SeriesInstanceUID | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')"

Unique_SeriesNumber=$(curl -s -H 'Content-Type: application/json' -XGET 'http://127.0.0.1:9200/image/image/_search' -d '
{
    "size" : 0,
    "aggs" : {
        "unique" : {
            "cardinality" : {
              "field" : "SeriesNumber.keyword"
            }
        }
    }
}' | jq .aggregations.unique.value)
 

echo "Unique SeriesNumber: $(echo $Unique_SeriesNumber | sed ':a;s/\B[0-9]\{3\}\>/,&/;ta')"

# Count Pixels
curl -s -X POST "localhost:9200/image/_search" -H 'Content-Type: application/json' --data-binary @count_pixel_agg.json | jq .aggregations.type_count.value

# Count header PHI
curl -s -H 'Content-Type: application/json' -XGET 'http://127.0.0.1:9200/count/count/_search' -d '
{
    "size" : 0,
    "query" : { "match": { "type": "header_PHI" } },
    "aggs" : {
        "header_PHI_count" : {
            "sum" : { 
                  "field": "count"
            }
          }
    }
}' | jq .

# Count all values in all fields
for FIELD_NAME in $(curl -s -XGET localhost:9200/image/_mapping | jq .image.mappings.image.properties | jq 'keys' | jq .[]); do FIELD_NAME=$(echo "$FIELD_NAME" | tr -d '"') ;  NUM_NOT_NULL=$(curl -s -X POST "localhost:9200/image/_search?size=0" -H 'Content-Type: application/json' -d'
{
    "aggs" : {
        "types_count" : { "value_count" : { "field" : "'$FIELD_NAME'.keyword" } }
    }
}
' | jq .aggregations.types_count.value);   echo "$NUM_NOT_NULL"; done > out 

paste -sd+ out | bc
