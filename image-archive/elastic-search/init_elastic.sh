#!/bin/bash

ELASTIC_IP="${ELASTIC_IP:-localhost}"
ELASTIC_PORT="${ELASTIC_PORT:-9200}"
ELASTIC_INDEX="${ELASTIC_INDEX:-image}"
ELASTIC_DOC_TYPE="${ELASTIC_DOC_TYPE:-image}"

# Create index
curl -s -H 'Content-Type: application/json' -X PUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX -w "\n" -d  @- << EOF
{
  "mappings": {
    "$ELASTIC_DOC_TYPE": {
      "date_detection": false,
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

curl -s -X POST http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_close -w "\n"

# followed by the actual addition of analyzers with:
curl -s -H 'Content-Type: application/json' -X PUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -w "\n" -d  @- << EOF
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

# Increase number of allowed fields
curl -H 'Content-Type: application/json' -XPUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -d '
{
  "index.mapping.total_fields.limit": 100000
}'

# Reduce replica count to 0 to prefer performance over availability
curl -H 'Content-Type: application/json' -XPUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -d '
{
    "index" : {
        "number_of_replicas" : 0
    }
}'

# followed by opening of the index. It is important to open the index up for any indexing and search operations to occur.
curl -s -X POST http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_open -w "\n"

##
## Create Reports Index
##

ELASTIC_INDEX="${REPORT_ELASTIC_INDEX:-report}"
ELASTIC_DOC_TYPE="${REPORT_ELASTIC_DOC_TYPE:-report}"

# Create index
curl -s -H 'Content-Type: application/json' -X PUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX -w "\n" -d  @- << EOF
{
  "mappings": {
    "$ELASTIC_DOC_TYPE": {
      "date_detection": false,
      "properties": {
        "body": {
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

curl -s -X POST http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_close -w "\n"

# followed by the actual addition of analyzers with:
curl -s -H 'Content-Type: application/json' -X PUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -w "\n" -d  @- << EOF
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

# Increase number of allowed fields
curl -H 'Content-Type: application/json' -XPUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -d '
{
  "index.mapping.total_fields.limit": 100000
}'

# Reduce replica count to 0 to prefer performance over availability
curl -H 'Content-Type: application/json' -XPUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -d '
{
    "index" : {
        "number_of_replicas" : 0
    }
}'

# followed by opening of the index. It is important to open the index up for any indexing and search operations to occur.
curl -s -X POST http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_open -w "\n"

##
## Create linking Index
##

ELASTIC_INDEX="${LINKING_ELASTIC_INDEX:-linking}"
ELASTIC_DOC_TYPE="${LINKING_ELASTIC_DOC_TYPE:-linking}"

# Create index

curl -s -H 'Content-Type: application/json' -X PUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX -w "\n" -d  @- << EOF
{
  "mappings": {
    "$ELASTIC_DOC_TYPE": {
      "date_detection": false,
      "properties": {
        "orig": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword"
            }
          }
        },
        "new": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword"
            }
          }
        }
      }
    }
  }
}
EOF

curl -s -X POST http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_close -w "\n"

# Reduce replica count to 0 to prefer performance over availability
curl -H 'Content-Type: application/json' -XPUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -d '
{
    "index" : {
        "number_of_replicas" : 0
    }
}'

# followed by opening of the index. It is important to open the index up for any indexing and search operations to occur.
curl -s -X POST http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_open -w "\n"


##
## Create COUNT Index
##

ELASTIC_INDEX="${COUNT_ELASTIC_INDEX:-count}"
ELASTIC_DOC_TYPE="${COUNT_ELASTIC_DOC_TYPE:-count}"

# Create index

curl -s -H 'Content-Type: application/json' -X PUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX -w "\n" -d  @- << EOF
{
  "mappings": {
    "$ELASTIC_DOC_TYPE": {
     "date_detection": false,
    }
  }
}
EOF

curl -s -X POST http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_close -w "\n"

# Reduce replica count to 0 to prefer performance over availability
curl -H 'Content-Type: application/json' -XPUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -d '
{
    "index" : {
        "number_of_replicas" : 0
    }
}'

# followed by opening of the index. It is important to open the index up for any indexing and search operations to occur.
curl -s -X POST http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_open -w "\n"
