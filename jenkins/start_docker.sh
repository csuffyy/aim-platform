#!/bin/bash
sudo docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e ES_JAVA_OPTS=$ES_JAVA_OPTS -v `pwd`/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml -v $ES_DATA_DIR:/usr/share/elasticsearch/data docker.elastic.co/elasticsearch/elasticsearch:6.6.0
