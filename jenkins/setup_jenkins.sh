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

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce

# install Tmuxinator (=>v0.11)
git clone https://github.com/tmuxinator/tmuxinator
cd tmuxinator
gem install tmuxinator
tmuxinator -v

# Setup Worker Node For Elastic
su ubuntu
mkdir ~/esdata
chown -R ubuntu:ubuntu ~/esdata

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
systemctl restart apache2

/etc/apache2/sites-enabled/images.conf
<VirtualHost *:80>
    ServerName images.ccm.sickkids.ca
    RewriteEngine On
    RewriteRule ^/(.*)$  https://%{HTTP_HOST}/$1 [QSA,R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName images.ccm.sickkids.ca
    Timeout 3000

    SSLEngine on
    SSLProtocol all -SSLv2 -SSLv3
    SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:!RC4+RSA:+HIGH:+MEDIUM:!LOW

    SSLCertificateFile /etc/cert/star_ccm_sickkids_ca.crt
    SSLCertificateKeyFile /etc/cert/star_ccm_sickkids_ca.key
    SSLCertificateChainFile /etc/cert/DigiCertCA.crt

    ProxyRequests Off
    <Proxy *>
        Order deny,allow
        Allow from all
    </Proxy>
    ProxyPreserveHost On
    ProxyPass / http://localhost:3000/
</VirtualHost>




<VirtualHost *:80>
    ServerName elastic.images.ccm.sickkids.ca
    RewriteEngine On
    RewriteRule ^/(.*)$  https://%{HTTP_HOST}/$1 [QSA,R=301,L]
</VirtualHost>

<VirtualHost *:443>
    ServerName elastic.images.ccm.sickkids.ca
    Timeout 3000

    SSLEngine on
    SSLProtocol all -SSLv2 -SSLv3
    SSLCipherSuite ALL:!ADH:!EXPORT:!SSLv2:!RC4+RSA:+HIGH:+MEDIUM:!LOW

    SSLCertificateFile /etc/cert/star_ccm_sickkids_ca.crt
    SSLCertificateKeyFile /etc/cert/star_ccm_sickkids_ca.key
    SSLCertificateChainFile /etc/cert/DigiCertCA.crt

    ProxyRequests Off
    <Proxy *>
        Order deny,allow
        Allow from all
    </Proxy>
    ProxyPreserveHost On
    ProxyPass / http://localhost:9200/
</VirtualHost>
