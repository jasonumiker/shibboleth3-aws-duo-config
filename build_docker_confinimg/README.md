# build_docker_confinimage
These configs and scripts will re-configure an upstream Dockerized Shibboleth (https://github.com/Unicon/shibboleth-idp-dockerized) project to work with AWS and Duo. The config, including the secrets, will be then be embedded in the container image produced. 

NOTE: This means that anybody who can pull the image will get the "keys to the kingdom" and so this is very sensitive. The way I've leveraged it is to build the image on the host(s) running it for now until I do the work to externalise the state to S3 in a secure way and pull it at runtime as required. I might also leverage the Parameter Store for some of the config or secrets as well.

## Usage
1. Edit the do_build.sh file and put the appropriate items into the variables at the top for your environment
1. Run do_build.sh as root or via sudo
1. It will produce an image locally called shibboleth:latest and a run.sh file that will run that image with the required options/environment variables passed in.