curl -s -X POST "localhost:9200/image/_search" -H 'Content-Type: application/json' --data-binary @count_pixel_agg.json | jq .aggregations.type_count.value