#!/bin/bash

#This script expects the following environment variables to be passed in
#idp_hostname=idp.DOMAIN.com
#idp_attributescope=DOMAIN.com
#idp_ldapURL=ldap://ad.DOMAIN.com:389
#idp_ldapbaseDN="CN=Users, DC=ad, DC=DOMAIN, DC=com"
#idp_ldapbindDN=shibboleth_svc@ad.DOMAIN.com
#idp_ldapdnFormat=%s@ad.DOMAIN.com
#idp_duo_apiHost=api-XXXXXXXX.duosecurity.com
#idp_duo_integrationKey=
#s3path=s3://jumiker-shibboleth-config/
#awsregion=ap-southeast-2

#Pick a couple random 32 character passwords for the build phase
idp_backchannel_password=$(cat /dev/urandom | env LC_CTYPE=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
idp_cookie_password=$(cat /dev/urandom | env LC_CTYPE=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

#Pick a random 40 character application key for Duo
idp_duo_applicationKey=$(cat /dev/urandom | env LC_CTYPE=C tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1)

#Do the 1st stage Docker build to generate the IdP's keys
docker build -f Dockerfile-config -t shibboleth-conf .
expect - <<EOF
spawn docker run -it -v $(pwd):/ext-mount --rm shibboleth-conf init-idp.sh
expect "Hostname:*"
send "$idp_hostname\r"
expect "Attribute Scope:*"
send "$idp_attributescope\r"
expect "SAML EntityID:*"
send "\r"
expect "Backchannel PKCS12 Password:"
send "$idp_backchannel_password\r"
expect "Re-enter password:"
send "$idp_backchannel_password\r"
expect "Cookie Encryption Key Password:"
send "$idp_cookie_password\r"
expect "Re-enter password:"
send "$idp_cookie_password\r"
expect "Most files, if not being customized can be removed from what was exported/the local Docker image and baseline files will be used."
EOF

#Update the config the 1st build exported to meet our needs
sed -i "/idp.encryption.optional/c\idp.encryption.optional= true" customized-shibboleth-idp/conf/idp.properties
sed -i "/idp.authn.flows= Password/c\idp.authn.flows= MFA" customized-shibboleth-idp/conf/idp.properties
sed -i s/$idp_cookie_password/SEALER_PASSWORD/g customized-shibboleth-idp/conf/idp.properties
sed -i "/idp.footer =/c\idp.footer = Shibboleth Federated Identity Provider" customized-shibboleth-idp/system/messages/messages.properties
sed -i "/root.footer =/c\root.footer = Shibboleth Federated Identity Provider" customized-shibboleth-idp/system/messages/messages.properties
sed -i "/idp.authn.LDAP.authenticator /c\idp.authn.LDAP.authenticator= adAuthenticator" customized-shibboleth-idp/conf/ldap.properties
sed -i "/idp.authn.LDAP.useStartTLS /c\idp.authn.LDAP.useStartTLS= false" customized-shibboleth-idp/conf/ldap.properties
sed -i "/idp.authn.LDAP.useSSL /c\idp.authn.LDAP.useSSL= false" customized-shibboleth-idp/conf/ldap.properties
sed -i "/idp.authn.LDAP.userFilter /c\idp.authn.LDAP.userFilter= (sAMAccountName={user})" customized-shibboleth-idp/conf/ldap.properties
sed -i "/idp.attribute.resolver.LDAP.searchFilter /c\idp.attribute.resolver.LDAP.searchFilter= (sAMAccountName=\$resolutionContext.principal)" customized-shibboleth-idp/conf/ldap.properties
sed -i "/idp.authn.LDAP.ldapURL /c\idp.authn.LDAP.ldapURL= $idp_ldapURL" customized-shibboleth-idp/conf/ldap.properties
sed -i "/idp.authn.LDAP.baseDN /c\idp.authn.LDAP.baseDN= $idp_ldapbaseDN" customized-shibboleth-idp/conf/ldap.properties
sed -i "/idp.authn.LDAP.bindDNCredential /c\idp.authn.LDAP.bindDNCredential= $idp_ldapbindDNCredential" customized-shibboleth-idp/conf/ldap.properties
sed -i "/idp.authn.LDAP.bindDN /c\idp.authn.LDAP.bindDN= $idp_ldapbindDN" customized-shibboleth-idp/conf/ldap.properties
sed -i "/idp.authn.LDAP.dnFormat /c\idp.authn.LDAP.dnFormat= $idp_ldapdnFormat" customized-shibboleth-idp/conf/ldap.properties
echo "idp.duo.apiHost = $idp_duo_apiHost" > customized-shibboleth-idp/conf/authn/duo.properties
echo "idp.duo.applicationKey = $idp_duo_applicationKey" >> customized-shibboleth-idp/conf/authn/duo.properties
echo "idp.duo.integrationKey = $idp_duo_integrationKey" >> customized-shibboleth-idp/conf/authn/duo.properties

#Compress up our config into a tgz for upload to S3
tar -zvcf customized-shibboleth-idp.tgz customized-shibboleth-idp

#Upload our config to S3
aws s3 cp customized-shibboleth-idp.tgz $s3path
aws s3 cp customized-shibboleth-idp/metadata/idp-metadata.xml $s3path

#Store our secrets in Parameter Store
aws --region $awsregion ssm put-parameter --name "/shibboleth/backchannel-password" --type "SecureString" --value $idp_backchannel_password --overwrite
aws --region $awsregion ssm put-parameter --name "/shibboleth/sealer-password" --type "SecureString" --value $idp_cookie_password --overwrite

#Clean up our config on the build server
rm -rf customized-shibboleth-id*
