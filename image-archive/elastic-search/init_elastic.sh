#!/bin/bash

# HOST_IP=192.168.136.128
HOST_IP="${HOST_IP:-localhost}"
echo $HOST_IP
ES_PORT=9200
INDEX_NAME=movie7

# Create index
curl -s -H 'Content-Type: application/json' -X PUT http://$HOST_IP:$ES_PORT/$INDEX_NAME -w "\n" -d  @- << EOF
{
  "mappings": {
    "tweet": {
      "properties": {
        "descriptions": {
          "type": "text",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "Modality": {
          "type": "text",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "StudyDescription": {
          "type": "text",
          "copy_to": "descriptions",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "ReasonForStudy": {
          "type": "text",
          "copy_to": "descriptions",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "SeriesDescription": {
          "type": "text",
          "copy_to": "descriptions",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "StudyComments": {
          "type": "text",
          "copy_to": "descriptions",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "Manufacturer": {
          "type": "text",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "InstitutionalDepartmentName": {
          "type": "text",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "InstitutionName": {
          "type": "text",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "BodyPartExamined": {
          "type": "text",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        },
        "PatientSex": {
          "type": "text",
          "fields": {
            "raw": {
              "type": "keyword"
            }
          },
          "analyzer": "standard"
        }
      }
    }
  }
}
EOF

curl -s -X POST http://$HOST_IP:$ES_PORT/$INDEX_NAME/_close -w "\n"

# followed by the actual addition of analyzers with:
curl -s -H 'Content-Type: application/json' -X PUT http://$HOST_IP:$ES_PORT/$INDEX_NAME/_settings -w "\n" -d  @- << EOF
{
  "analysis" : {
    "analyzer":{
        "autosuggest_analyzer": {
            "filter": [
                "lowercase",
                "asciifolding",
                "autosuggest_filter"
            ],
            "tokenizer": "standard",
            "type": "custom"
        },
        "ngram_analyzer": {
            "filter": [
                "lowercase",
                "asciifolding",
                "ngram_filter"
            ],
            "tokenizer": "standard",
            "type": "custom"
        }
    },
    "filter": {
        "autosuggest_filter": {
            "max_gram": "20",
            "min_gram": "1",
            "token_chars": [
                "letter",
                "digit",
                "punctuation",
                "symbol"
            ],
            "type": "edge_ngram"
        },
        "ngram_filter": {
            "max_gram": "9",
            "min_gram": "2",
            "token_chars": [
                "letter",
                "digit",
                "punctuation",
                "symbol"
            ],
            "type": "ngram"
        }
    }
  }
}
EOF

# followed by opening of the index. It is important to open the index up for any indexing and search operations to occur.
curl -s -X POST http://$HOST_IP:$ES_PORT/$INDEX_NAME/_open -w "\n"

# curl -s -H 'Content-Type: application/json' -X PUT http://$HOST_IP:$ES_PORT/$INDEX_NAME/_mapping/tweet -w "\n" -d  @- << EOF
# {
#   "properties": {
#     "Modality": {
#       "type": "text",
#       "fields": {
#         "autosuggest": {
#           "type": "text",
#           "analyzer": "autosuggest_analyzer",
#           "search_analyzer": "simple"
#         }
#       }
#     }
#   }
# }
# EOF

curl -s -X GET http://$HOST_IP:$ES_PORT/$INDEX_NAME | jq


