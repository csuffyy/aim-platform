# AIM Tunnel to get a static file webserver on port 8000 out of HPF through port 22 to Openstack port 8000
# Run on data1.ccm.sickkids.ca
ssh -fNq -R 0.0.0.0:8000:localhost:8000 ubuntu@172.20.4.83

# AIM tunnel elasticsearch running on OpenStack VM (port 9200) to HPF data server (port 9200)
# Run on hpf23.ccm.sickkids.ca
ssh -fNq -L 0.0.0.0:9200:localhost:9200 ubuntu@172.20.4.83

# AIM Tunnel to get a static file webserver on port 8000 out of HPF through port 22 to Openstack port 8000 via desktop
# Run on desktop workstation
# ssh -L 8000:localhost:8000 dsnider@data1.ccm.sickkids.ca
# ssh -R 8000:localhost:8000 ubuntu@172.20.4.85

## (Retired) AIM tunnel elasticsearch running on OpenStack VM (port 9200) to HPF data server (port 9200) via my workstation
# Run on desktop workstation
#ssh -R 9090:172.20.4.85:9200 dsnider@data1.ccm.sickkids.ca "ssh -g -N -L 9200:localhost:9090 localhost"