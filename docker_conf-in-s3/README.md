# docker_conf-in-s3
These configs and scripts will re-configure an upstream Dockerized Shibboleth (https://github.com/Unicon/shibboleth-idp-dockerized) project to work with AWS and Duo. The config will be stored in S3 and the password to unlock the backchannel certificate is stored encyrpted in Parameter Store.

## Usage
1. Have a working AD - I used AWS' Simple AD service for this with the CloudFormation template in this project
    1. Set up the following in that directory:
        1. A user account for Shibboleth to validate users/groups (I used shibboleth_svc)
        1. A group for each role that you want users to be able to assume in AWS in the format AWS-AccountNumber-Rolename
        1. Any users to use this need to have a valid email address on their account (it'll map that to awsRoleSessionName)
1. Have a working Duo account (the Duo Free tier is fine)
    1. In that account add a Shibboleth Application and note the Integration Key, Secret Key and Hostname
1. Edit the build_conf.sh file and put the appropriate items into the variables at the top for your environment
1. Run build_conf.sh and make sure to note the two passwords output at the end - we'll need to put those into Parameter Store
1. It will produce a config with the required certificates and configuration as well as tgz that up - put that customized-shibboleth-idp.tgz in an S3 bucket restricted to the instance/task IAM role of the host/container
1. Edit the run-jetty.sh file with the S3 path for this container to pull the config tgz at runtime
1. Put the following secrets in the Parameter Store
	1. Backchannel password from end of the build_conf.sh output as /shibboleth/backchannel-password
	1. Sealer password from end of the build_conf.sh output as /shibboleth/sealer-password
	1. LDAP Bind Password as /shibboleth/ldap-password
	1. Duo Secret Key as /shibboleth/duo-secretKey
1. Build the container image by running build_runtime_image.sh and push that up to your registry of choice
1. In AWS go to IAM -> Identity Providers and add a new SAML one called Shibboleth.
    1. The Metadata XML to use was generated as part of the container build and will be in the customized-shibboleth-idp/metadata folder on the machine that did the build as well as in the tgz file you put in S3 if that is no longer available.
1. Create an ELB or ALB pointing HTTPS publicly to HTTP 8080 on your local server
    1. Ideally you can use the ACM service to generate/maintain the cert to terminate encryption
    1. Turn on stickiness - I chose 5 minutes as the timeframe and that seems to work well. We just want to makes sure a particular user sticks with one task for the whole login processs
1. (Optionally) Leverage the nginx_redirect conainer we built by:
	1. Using an ALB to the root path (/) to 8888 on that container and it'll redirect you to the full path with a 302
	1. Send everything else straight to the shibboleth container on 8080
