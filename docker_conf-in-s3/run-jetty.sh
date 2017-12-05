#!/bin/sh

#set -x
# Bootstrapping script for Shibboleth container
# This script expects the following environment variables to be passed to the container
# S3PATH e.g. s3://sydney-shib-build-configbucket/customized-shibboleth-idp.tgz

export JAVA_HOME=/opt/jre-home
export PATH=$PATH:$JAVA_HOME/bin

# Determine what region we are in and save that as AWSREGION
export AWSREGION =$(curl -s 169.254.169.254/latest/meta-data/placement/availability-zone | sed 's/.$//')

# Download the config from S3PATH to /tmp and then move it to /opt/shibboleth-idp
cd /tmp
aws s3 cp $S3PATH .
tar -zvxf customized-shibboleth-id*.tgz
cp -R customized-shibboleth-idp/* /opt/shibboleth-idp/
rm -rf customized-shibboleth-idp

# Retrieve the secrets from SSM Parameter Store and store them as variables
backchannel_password=$(aws ssm get-parameters --region $AWSREGION --with-decryption --names /shibboleth/backchannel-password | jq -r '.Parameters[0].Value')
sealer_password=$(aws ssm get-parameters --region $AWSREGION --with-decryption --names /shibboleth/sealer-password | jq -r '.Parameters[0].Value')
ldap_password=$(aws ssm get-parameters --region $AWSREGION --with-decryption --names /shibboleth/ldap-password | jq -r '.Parameters[0].Value')
duo_secretKey=$(aws ssm get-parameters --region $AWSREGION --with-decryption --names /shibboleth/duo-secretKey | jq -r '.Parameters[0].Value')

# Put the secrets in the appropriate places
export JETTY_ARGS="jetty.backchannel.sslContext.keyStorePassword=$backchannel_password"
sed -i s/SEALER_PASSWORD/$sealer_password/g /opt/shibboleth-idp/conf/idp.properties
sed -i s/LDAP_PASSWORD/$ldap_password/g /opt/shibboleth-idp/conf/ldap.properties
echo "idp.duo.secretKey = $duo_secretKey" >> /opt/shibboleth-idp/conf/authn/duo.properties

sed -i "s/^-Xmx.*$/-Xmx$JETTY_MAX_HEAP/g" /opt/shib-jetty-base/start.ini

exec /etc/init.d/jetty run
