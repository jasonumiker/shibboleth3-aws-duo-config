#!/bin/sh

#set -x

export JAVA_HOME=/opt/jre-home
export PATH=$PATH:$JAVA_HOME/bin

cd /tmp
aws s3 cp s3://jumiker-shibboleth-config/customized-shibboleth-idp.tgz .
tar -zvxf customized-shibboleth-idp.tgz
cp -R customized-shibboleth-idp/* /opt/shibboleth-idp/
rm -rf customized-shibboleth-idp

backchannel_password=$(aws ssm get-parameters --region ap-southeast-2 --with-decryption --names /shibboleth/backchannel-password | jq -r '.Parameters[0].Value')

export JETTY_ARGS="jetty.backchannel.sslContext.keyStorePassword=$backchannel_password"
sed -i "s/^-Xmx.*$/-Xmx$JETTY_MAX_HEAP/g" /opt/shib-jetty-base/start.ini

exec /etc/init.d/jetty run
