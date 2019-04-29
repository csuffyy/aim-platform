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


