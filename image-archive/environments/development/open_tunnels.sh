# AIM Tunnel to get a static file webserver on port 8000 out of HPF through port 22 to Openstack port 8000
ssh -L 8000:localhost:8000 dsnider@data1.ccm.sickkids.ca
ssh -R 8000:localhost:8000 ubuntu@172.20.4.85

# AIM tunnel elasticsearch running on OpenStack VM (port 9200) to HPF data server (port 9200) via my workstation
ssh -R 9090:172.20.4.85:9200 dsnider@data1.ccm.sickkids.ca "ssh -g -N -L 9200:localhost:9090 localhost"