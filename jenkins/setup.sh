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

openstack server create --flavor plaussenlab-ws --image Ubuntu-Server-18.04-2018Sep19 --security-group 9200 --security-group default --security-group ssh_22 --key-name Daniel-CCM --network test_network $INSTANCE_NAME
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

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce
