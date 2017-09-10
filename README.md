# shibboleth3-aws-duo-config
This project is to help to deploy a Shibboleth IdP for SAML Federation and Single-Sign-On (SSO) to AWS with Duo two-factor enabled. 

Login Screen (with your AD credentials)
![login](login.PNG)

Duo 2nd Authentication Factor
![duo](duo.PNG)

Once you have a working Shibboleth you can use this other project I've been working on to access the AWS CLI via the IdP with the 2nd factor as well - https://github.com/jasonumiker/samlapi

## Usage
There are three methods I've documented or automated so far:
1. You can install the package on a Windows server and then manually modify the configuration files as described in the manual_config_windows folder. This config should mostly work on Linux as well but the paths are slightly different there.
1. You can use the scripts and configuration files in docker_conf-in-img project to build a Linux Docker image with all the configs required embedded in the image.
1. You can externalise the configuration and secrets to S3 and Parameter store and build a container that will pull them at runtime by using docker_conf-in-s3.

WARNING: The in-image Dockerized config includes the secrets so you need to either do this build locally on the machine that will run the container/service or secure the pulling of the image to trusted individuals. The private keys in this config can be exploited to get extensive AWS access if leaked. These keys will also be in the customized-shibboleth-idp folder that is part of the build process on the server that did the build so clean them up afterward if required for safety.

## Assumptions
1. I built this against a Simple AD which does not use SSL to secure the LDAP communication involved for example. The LDAP config against a 'true' MS AD server will likely require some changes.
1. I leveraged the built-in Duo MFA plugin in the Shibboleth so the assumption is that you want to leverage Duo at the moment. They do support other MFA types via plugins and I have not yet explored that.

## Future plans
Things to come for this project include:
1. Testing and parameters to handle connecting to MS AD servers instead of Simple AD (you'd likely have to set up a trust of the AD's certificates etc.)
1. Support for more MFA plugins/types including at least Google Authenticator or opting-out of MFA to just use Passwords if you want
1. CloudFormation templates to roll this out including one for setting up EC2 instances to run this container and another for Deploying it to ECS
