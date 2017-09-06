# build_docker_confinimage
These configs and scripts will re-configure an upstream Dockerized Shibboleth (https://github.com/Unicon/shibboleth-idp-dockerized) project to work with AWS and Duo. The config, including the secrets, will be then be embedded in the container image produced. 

NOTE: This means that anybody who can pull the image will get the "keys to the kingdom" and so this is very sensitive. The way I've leveraged it is to build the image on the host(s) running it for now until I do the work to externalise the state to S3 in a secure way and pull it at runtime as required. I might also leverage the Parameter Store for some of the config or secrets as well.

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
1. Create an ELB or ALB pointing HTTPS publicly to HTTP 8080 on your local server
    1. Ideally you can use the ACM service to generate/maintain the cert to terminate encryption
    1. For bonus points you can create an nginx or Apache sidecar container listening on another port that redirects / to https://idp.mydomain.com/idp/profile/SAML2/Unsolicited/SSO?providerId=urn:amazon:webservices and then two ALB listener rules - one that sends / to the sidecar's port and everything else to 8080 on the backend
        1. That means you can go to https://idp.mydomain.com and it'll get you to the right place