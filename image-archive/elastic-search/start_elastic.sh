#!/bin/bash
sudo docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e ES_JAVA_OPTS="-Xms16g -Xmx16g" -v `pwd`/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml -v /home/ubuntu/esdata:/usr/share/elasticsearch/data docker.elastic.co/elasticsearch/elasticsearch:6.7.1
