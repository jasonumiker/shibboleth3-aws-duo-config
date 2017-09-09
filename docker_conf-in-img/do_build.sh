#!/bin/bash

#Set up the variables to configure our environment
idp_hostname=idp.DOMAIN.com
idp_attributescope=DOMAIN.com
idp_ldapURL=ldap://ad.DOMAIN.com:389
idp_ldapbaseDN="CN=Users, DC=ad, DC=DOMAIN, DC=com"
idp_ldapbindDN=shibboleth@ad.DOMAIN.com
idp_ldapbindDNCredential=PASSWORD
idp_ldapdnFormat=%s@ad.DOMAIN.com
idp_duo_apiHost=api-XXXXXXXX.duosecurity.com
idp_duo_applicationKey=$(cat /dev/urandom | env LC_CTYPE=C tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1)
idp_duo_integrationKey=DUOINTKEY
idp_duo_secretKey=DUOSECRETKEY
buildpath=/home/ec2-user/shibboleth3-aws-duo-config/build_docker_confinimg
#buildpath=/Users/jumiker/shibboleth3-aws-duo-config/build_docker_confinimg

#Pick a couple random 32 character passwords for the build phase
idp_backchannel_password=$(cat /dev/urandom | env LC_CTYPE=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
idp_cookie_password=$(cat /dev/urandom | env LC_CTYPE=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

#Clean up any previous builds
docker rmi shibboleth
cd $buildpath
rm -rf customized-shibboleth-idp

#Do the 1st stage Docker build to generate the IdP's keys
docker build -t shibboleth .
expect - <<EOF
spawn docker run -it -v $(pwd):/ext-mount --rm shibboleth init-idp.sh
expect "Hostname:*"
send "$idp_hostname\r"
expect "Attribute Scope:*"
send "idp_attributescope\r"
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
echo "idp.duo.secretKey = $idp_duo_secretKey" >> customized-shibboleth-idp/conf/authn/duo.properties

#Do the second stage Docker build to overwrite that customised config into the image
cp Dockerfile-stage2 customized-shibboleth-idp/Dockerfile
cd customized-shibboleth-idp
docker build -t shibboleth .

#Create the run.sh
echo "docker run -d --name="shibboleth" --rm -p 8080:8080 -e JETTY_BACKCHANNEL_SSL_KEYSTORE_PASSWORD=$idp_backchannel_password shibboleth run-jetty.sh" > ../run.sh
echo "docker run -d --name"nginx_redirect" --rm -p 8888:80 nginx_redirect" >> .$
chmod u+x ../run.sh

#Modify the redirect container
sed -i "/return 301/c\             return 301 https://$idp_hostname/idp/profile$

#Build the redirect container
cd ../redirect_container
docker build -t nginx_redirect .
