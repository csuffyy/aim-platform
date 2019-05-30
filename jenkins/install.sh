#!/bin/bash

###############################
# Jenkins Dependencies
###############################

# Source OpenStack CLI info
export OS_USERNAME=
export OS_PASSWORD=
export OS_TENANT_NAME=HSC_CCM_PhenoTips
export OS_AUTH_URL=https://os.hpc4health.ca:5000/v3/
export OS_PROJECT_DOMAIN_NAME="Default"
export OS_USER_DOMAIN_NAME="Default"
export OS_IDENTITY_API_VERSION=3

# Create Jenkins VM
INSTANCE_NAME='AIM-Jenkins'
FLOATING_IP='172.20.4.43'
openstack server create --flavor m1.medium --image Ubuntu-Server-18.04-2018Sep19 --security-group pathway-demo_8080 --security-group default --security-group ssh_22 --key-name Daniel-CCM --network test_network $INSTANCE_NAME
# Wait for instance to get an internal IP before adding a float
openstack server add floating ip $INSTANCE_NAME $FLOATING_IP

# Create Development VM
INSTANCE_NAME='AIM-Elastic-Dev'
FLOATING_IP='172.20.4.85'

openstack server create --flavor plaussenlab-ws --image Ubuntu-Server-18.04-2018Sep19 --security-group 9200 --security-group default --security-group ssh_22 --security-group 8080 --security-group 8000 --key-name Daniel-CCM --network test_network $INSTANCE_NAME
# Wait for instance to get an internal IP before adding a float
openstack server add floating ip $INSTANCE_NAME $FLOATING_IP

# Login
ssh -i ~/.ssh/id_rsa_CCM ubuntu@$FLOATING_IP
ssh -i ~/.ssh/id_rsa_CCM ubuntu@172.20.4.85

# Install
sudo apt install openjdk-8-jre
wget -q -O - https://pkg.jenkins.io/debian/jenkins-ci.org.key | sudo apt-key add -
sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'
sudo apt-get update
sudo apt-get install jenkins
# sudo service jenkins restart
sudo service jenkins status
tail /var/log/jenkins/jenkins.log

# First Time Setup
PASSWORD=`cat /var/lib/jenkins/secrets/initialAdminPassword`
open $FLOATING_IP:8080
# enter PASSWORD and install reccommended plugins
# create admin user:
# Username: ccm
# Password: 
# Optionally Install Blue Ocean plugin
# http://172.20.4.43:8080/blue/

# In Jenkins go to
# http://172.20.4.43:8080/scriptApproval/
# Add Signatures approvals:
# method hudson.model.AbstractCIBase getComputer hudson.model.Node
# method java.net.InetAddress getCanonicalHostName
# method java.net.InetAddress getHostAddress
# method jenkins.scm.RunWithSCM getChangeSets
# method org.jenkinsci.plugins.workflow.support.steps.build.RunWrapper getRawBuild
# staticMethod java.net.InetAddress getLocalHost
# staticMethod jenkins.model.Jenkins getInstance
# staticMethod org.codehaus.groovy.runtime.DefaultGroovyMethods getAt java.lang.Object java.lang.String

###############################
# Application Dependencies
###############################

# Download our project code
cd ~
git clone https://github.com/aim-sk/aim-platform

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce

# System config settings
echo vm.max_map_count=262144 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p    # for Elastic Compute
echo fs.inotify.max_user_watches=582222 | sudo tee -a /etc/sysctl.conf && sudo sysctl -p    # for NodeJS to watch more files

# Allow running docker commands without sudo (for local development ONLY, used for simple automation)
sudo groupadd docker
sudo usermod -aG docker $USER
docker run hello-world # if this doesn't work and asks for permissions, do the next command "gnome-session-quit"
# gnome-session-quit --no-prompt # this will log you out, you'll have to log back in


# Install Tmuxinator (=>v0.11)
git clone https://github.com/tmuxinator/tmuxinator
cd tmuxinator
gem install tmuxinator
tmuxinator -v

# Install deid dependencies (python and etc.)
sudo apt-get install -y python3-tk # for matplotlib
sudo apt-get install -y python3.7-dev libpython3.7-dev python3-pip
# sudo pip3 install virtualenv
# virtualenv -p python3.7 venv
# cd venv/
# . bin/activate
pip3.7 install numpy IPython scikit-image matplotlib pandas Pillow click pydicom deid pytesseract opencv-python python-Levenshtein fuzzywuzzy fuzzywuzzy[speedup] elasticsearch dateparser

pip3.7 install --user Pillow==5.2.0
apt-get install python-apt

wget https://github.com/tesseract-ocr/tessdata/blob/master/eng.traineddata?raw=true
sudo cp eng.traineddata?raw=true /usr/share/tesseract-ocr/4.00/tessdata/eng.traineddata


# Install GDCM
sudo apt-get install python-gdcm # for pydicom
git clone --branch master https://github.com/HealthplusAI/python3-gdcm.git && cd python3-gdcm && dpkg -i build_1-1_amd64.deb && apt-get install -f
sudo cp /usr/local/lib/gdcm.py /usr/local/lib/python3.7/dist-packages/
sudo cp /usr/local/lib/gdcmswig.py /usr/local/lib/python3.7/dist-packages/
sudo cp /usr/local/lib/_gdcmswig.so /usr/local/lib/python3.7/dist-packages/
sudo cp /usr/local/lib/libgdcm* /usr/local/lib/python3.7/dist-packages/

# cp /usr/local/lib/gdcm.py ./lib/python3.7/site-packages/
# cp /usr/local/lib/gdcmswig.py ./lib/python3.7/site-packages/
# cp /usr/local/lib/_gdcmswig.so ./lib/python3.7/site-packages/
# cp /usr/local/lib/libgdcm* ./lib/python3.7/site-packages/

# Developer helper tools:
# sudo apt-get install vtk-dicom-tools
# dicomdump file1.dcm

# Install Yarn
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
sudo apt update
sudo apt install yarn nodejs
cp -r image-archive/reactive-search/appbase-js/* image-archive/reactive-search/node_modules/appbase-js/

# Start our entire application 
cd ~/aim-platform/image-archive
./start_aim.sh


###############################
# Install Imaging Archive
###############################

#Install ElasticSearch
cd image-archive/elastic-search/
sudo docker rm -f elasticsearch || true
./start_elastic.sh
bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:9200`" != "200" ]]; do echo "trying again"; sleep 5; done; curl localhost:9200; echo "ELASTIC UP"'
sudo docker logs elasticsearch
./init_elastic.sh

#Install DWV
cd image-archive/dwv/
yarn install
yarn run start &
bash -c 'while [[ "`curl -v -s -o /dev/null -w ''%{http_code}'' localhost:8080`" != "200" ]]; do echo "trying again"; sleep 5; done; curl localhost:8080; echo "DWV UP"'

#Install ReactiveSearch
cd image-archive/reactive-search/
npm install --verbose --color false 2>&1
patch --verbose --ignore-whitespace -p 10 -F 10 node_modules/@appbaseio/reactivesearch/lib/server/index.js < server-side-provide-headers-to-elastic.patch
patch --verbose --ignore-whitespace -p 10 -F 10 node_modules/@appbaseio/reactivesearch/lib/components/result/ReactiveList.js < comma-seperated-numbers.patch
patch --verbose --ignore-whitespace -p 10 -F 10 ~/dwv-jqmobile/node_modules/dwv/dist/dwv.js < 0001-increased-text-limit-to-65000.patch
patch --verbose --ignore-whitespace -p 10 -F 10 ~/.local/lib/python3.7/site-packages/datefinder/constants.py < find-all-dates.patch
patch --verbose --ignore-whitespace -p 10 -F 10 ~/.local/lib/python3.7/site-packages/datefinder/__init__.py < overflowerror-fix.patch
npm run dev &
cp -r image-archive/reactive-search/appbase-js/* image-archive/reactive-search/node_modules/appbase-js/

###############################
# Production Server Dependencies
###############################

# Create elastic folder
su ubuntu
mkdir ~/esdata
chown -R ubuntu:ubuntu ~/esdata

# Add names to enterprise DNS
elasticimages.ccm.sickkids.ca ---> 172.20.4.83
dwvimages.ccm.sickkids.ca ---> 172.20.4.83
staticimages.ccm.sickkids.ca ---> 172.20.4.83

devimages.ccm.sickkids.ca ---> 172.20.4.85
develasticimages.ccm.sickkids.ca ---> 172.20.4.85
devdwvimages.ccm.sickkids.ca ---> 172.20.4.85
devstaticimages.ccm.sickkids.ca ---> 172.20.4.85

#/etc/hosts
127.0.0.1 localhost images.ccm.sickkids.ca elasticimages.ccm.sickkids.ca dwvimages.ccm.sickkids.ca staticimages.ccm.sickkids.ca

# Set hostname
hostname images.ccm.sickkids.ca
sudo echo images.ccm.sickkids.ca > /etc/hostname

# apache SSL gateway
apt-get install apache2
sudo ufw allow 'Apache'
sudo systemctl status apache2
sudo a2enmod rewrite
sudo a2enmod ssl
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
systemctl restart apache2

# Install Apache conf for SSL/https proxy
cp aim-platform/image-archive/environments/production/apache-https-proxy.conf /etc/apache2/sites-enabled/images.conf
systemctl restart apache2


# install secrets
sudo echo "export AUTH_TOKEN='771100'" > /etc/secrets.sh
sudo echo "export FILESERVER_TOKEN='771100'" > /etc/secrets.sh

# Make colour of bottom bar on Tmux red
cat <<EOT>> ~/.tmux.conf
set -g default-terminal "screen-256color"
set -g status-bg red
set -g status-fg white
EOT