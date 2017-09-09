# build_docker_confinimage
These configs and scripts will re-configure an upstream Dockerized Shibboleth (https://github.com/Unicon/shibboleth-idp-dockerized) project to work with AWS and Duo. The config, including the secrets, will be then be embedded in the container image produced. 

WARNING: This means that anybody who can see the artefacts generated in customized-shibboleth-idp on the system that did the build or can pull the image will get the "keys to the kingdom" and so this is very sensitive. The way I've leveraged it is to build the image on the host(s) running it for now until I do the work to externalise the state to S3 in a secure way and pull it at runtime as required. I might also leverage the Parameter Store for some of the config or secrets as well.

## Usage
1. Have a working AD - I used AWS' Simple AD service for this with the CloudFormation template in this project
    1. Set up the following in that directory:
        1. A user account for Shibboleth to validate users/groups (I used shibboleth_svc)
        1. A group for each role that you want users to be able to assume in AWS in the format AWS-AccountNumber-Rolename
        1. Any users to use this need to have a valid email address on their account (it'll map that to awsRoleSessionName)
1. Have a working Duo account (the Duo Free tier is fine)
    1. In that account add a Shibboleth Application and note the Integration Key, Secret Key and Hostname
1. Edit the do_build.sh file and put the appropriate items into the variables at the top for your environment
1. Run do_build.sh as root or via sudo
1. It will produce an image locally called shibboleth:latest and a run.sh file that will run that image with the required options/environment variables passed in.
1. In AWS go to IAM -> Identity Providers and add a new SAML one called Shibboleth.
    1. The Metadata XML to use was generated as part of the container build and will be in the customized-shibboleth-idp/metadata folder on the machine that did the build
1. Create an ELB or ALB pointing HTTPS publicly to HTTP 8080 on your local server
    1. Ideally you can use the ACM service to generate/maintain the cert to terminate encryption
1. (Optionally) Leverage the nginx_redirect conainer we built by:
    1. Having a seperate ALB target group on the root path (/) pointing to 8888 on that container to 302 redirect you to the full path
    1. Send everything else to the shibboleth container/service on 8080 via another target group
