env.PUBLIC_IP='172.20.4.85'
env.ELASTIC_IP='172.20.4.85'
env.FALLBACK_ELASTIC_IP='172.20.4.85'
env.FALLBACK_ELASTIC_PORT=9200
env.ELASTIC_PORT=9200
env.ELASTIC_INDEX='image'
env.ELASTIC_DOC_TYPE='image'
env.REPORT_ELASTIC_INDEX='report'
env.REPORT_ELASTIC_DOC_TYPE='report'
env.ES_JAVA_OPTS='-Xms16g -Xmx16g'
env.FILESERVER_IP='172.20.4.85'
env.FILESERVER_PORT='3000'
env.FILESERVER_TOKEN='' // NOTE: groovy load sucks and doesn't want to set an empty environment variable, it would rather the variable not exist :-X
env.FILESERVER_DICOM_PATH='static/dicom'
env.FILESERVER_THUMBNAIL_PATH='static/thumbnails'
env.AUTH_TOKEN='771100'
