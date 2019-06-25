export ENVIRON='production'
export PUBLIC_IP='172.20.8.15'
export ELASTIC_IP='172.20.8.15'
export FALLBACK_ELASTIC_IP='172.20.8.15'
export FALLBACK_ELASTIC_PORT=9200
export ELASTIC_PORT=9200
export ELASTIC_INDEX='deid_image'
export ELASTIC_DOC_TYPE='deid_image'
export ELASTIC_URL='https://elasticimages.ccm.sickkids.ca'
export LINKING_ELASTIC_INDEX='linking'
export LINKING_ELASTIC_DOC_TYPE='linking'
export REPORT_ELASTIC_INDEX='report'
export REPORT_ELASTIC_DOC_TYPE='report'
export ES_JAVA_OPTS='-Xms32g -Xmx32g'
export FILESERVER_IP='172.20.8.15'
export FILESERVER_PORT='8000'
export FILESERVER_DICOM_PATH='/hpf/largeprojects/diagimage_common/'
export FILESERVER_THUMBNAIL_PATH='shared/thumbnails'
export AUTH_TOKEN='771100'
export FILESERVER_TOKEN=''
export STATIC_WEBSERVER_URL='https://staticimages.ccm.sickkids.ca/'
export DWV_URL='https://dwvimages.ccm.sickkids.ca/'
source /etc/secrets.sh


# # Create index
# curl -s -H 'Content-Type: application/json' -X PUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX -w "\n" -d  @- << EOF
# {
#   "mappings": {
#     "$ELASTIC_DOC_TYPE": {
#       "date_detection": false,
#       "properties": {
#         "descriptions": {
#           "type": "text",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "Modality": {
#           "type": "text",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "StudyDescription": {
#           "type": "text",
#           "copy_to": "descriptions",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "ReasonForStudy": {
#           "type": "text",
#           "copy_to": "descriptions",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "SeriesDescription": {
#           "type": "text",
#           "copy_to": "descriptions",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "StudyComments": {
#           "type": "text",
#           "copy_to": "descriptions",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "Manufacturer": {
#           "type": "text",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "InstitutionalDepartmentName": {
#           "type": "text",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "InstitutionName": {
#           "type": "text",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "BodyPartExamined": {
#           "type": "text",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         },
#         "PatientSex": {
#           "type": "text",
#           "fields": {
#             "raw": {
#               "type": "keyword"
#             }
#           },
#           "analyzer": "standard"
#         }
#       }
#     }
#   }
# }
# EOF

# curl -s -X POST http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_close -w "\n"

# # followed by the actual addition of analyzers with:
# curl -s -H 'Content-Type: application/json' -X PUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -w "\n" -d  @- << EOF
# {
#   "analysis" : {
#     "analyzer":{
#         "autosuggest_analyzer": {
#             "filter": [
#                 "lowercase",
#                 "asciifolding",
#                 "autosuggest_filter"
#             ],
#             "tokenizer": "standard",
#             "type": "custom"
#         },
#         "ngram_analyzer": {
#             "filter": [
#                 "lowercase",
#                 "asciifolding",
#                 "ngram_filter"
#             ],
#             "tokenizer": "standard",
#             "type": "custom"
#         }
#     },
#     "filter": {
#         "autosuggest_filter": {
#             "max_gram": "20",
#             "min_gram": "1",
#             "token_chars": [
#                 "letter",
#                 "digit",
#                 "punctuation",
#                 "symbol"
#             ],
#             "type": "edge_ngram"
#         },
#         "ngram_filter": {
#             "max_gram": "9",
#             "min_gram": "2",
#             "token_chars": [
#                 "letter",
#                 "digit",
#                 "punctuation",
#                 "symbol"
#             ],
#             "type": "ngram"
#         }
#     }
#   }
# }
# EOF

# # Increase number of allowed fields
# curl -s -H 'Content-Type: application/json' -XPUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -d '
# {
#   "index.mapping.total_fields.limit": 100000
# }'

# # Reduce replica count to 0 to prefer performance over availability
# curl -s -H 'Content-Type: application/json' -XPUT http://$ELASTIC_IP:$ELASTIC_PORT/$ELASTIC_INDEX/_settings -d '
# {
#     "index" : {
#         "number_of_replicas" : 0
#     }
# }'
