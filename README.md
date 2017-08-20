# shibboleth3-aws-duo-config
This is a sample config for setting up Shibboleth v3 to federate with AWS via SAML with a Duo MFA enabled.

It was developed on Windows with the options to install Jetty and Configure for Active Directory as described here:
https://wiki.shibboleth.net/confluence/display/IDP30/WindowsInstallation

I am planning on also trying it on Linux using this containerised approach as a base next and will update this with any changes required to deploy that way instead:
https://github.com/Unicon/shibboleth-idp-dockerized 

The instructions on how to set up Shibboleth in this way are:
1. Have a working AD - I used AWS' Simple AD service for this with the CloudFormation template in this project
    1. Set up the following in that directory:
        1. A user account for Shibboleth to validate users/groups (I used shibboleth_svc)
        1. A group for each role that you want users to be able to assume in AWS in the format AWS-Groupname
        1. Any users to use this need to have a valid email address on their account (it'll map to awsRoleSessionName)
1. Have a working Duo account (the Duo Free up to 10 users is fine)
    1. In that account add a Shibboleth Application and note the Integration Key, Secret Key and Hostname
1. Install the appropriate Oracle Java runtime and set the JAVA_HOME environmental variable to point to the installation (My Computer->RightClick->Properties->Advanced System Settings->Environmental Variables->System Variables->New)
1. Download the latest Shibboleth IdP from here and run the MSI - https://shibboleth.net/downloads/identity-provider/latest/
    1. Click to install Jetty and Cofigure for Active Directory
    1. Put the DNS resolvable address of your Shibboleth. I used idp.mydomain.com. This guide will point this address at a load balancer later rather than the address of the server directly.
    1. The scope of the IdP will be your domain name like mydomain.com
    1. The Active Directory Domain will be the name Directory DNS address (in my case ad.mydomain.com)
    1. Then, finally the username and password of the service account created above (in my case shibboleth_svc)
1. Edit the files above as follows:
    1. Put the Duo properties in the duo.properties file
        1. The Application Secret or akey needs to be a random string at least 40 characters long.
            1. You can generate it with the following Python for example:
                ```
                import os, hashlib
                print hashlib.sha1(os.urandom(32)).hexdigest()
                ```
    1. In attribute-resolver.xml replace XXXXXXXXXXXX with your AWS Account Number
    1. In idp.properties update the entityId and scope with your domain name and the store and key passwords from the install's idp.properties
    1. In ldap.properties update the DOMAIN names and the bindDNCredential with your service account password
    1. In jetty-base/start.d/idp.ini update it with backchannel and browser keystore passwords from the install's idp.ini
1. Overwrite the files in the default install with the files from this repo. I'd back them all up with a .orig on the end first.
1. In AWS go to IAM -> Identity Providers and add a new SAML one called Shibboleth.
    1. The Metadata XML to use was generated on install and is at C:\Program Files (x86)\Shibboleth\IdP\metadata\idp-metadata.xml
1. Under IAM -> Roles create a new Role for identity provider access. Pick the Grant Web Single Sign-On (WebSSO) access to SAML providers. Make sure to call the role Shibboleth-Rolename e.g. Shibboleth-Admins
1. Restart the service in services.msc (it is called Shibboleth)
1. Add the name you used (mine was idp.mydomain.com) to c:\windows\system32\drivers\hosts to the local server IP for testing
1. Go to http://idp.mydomain.com/idp/profile/SAML2/Unsolicited/SSO?providerId=urn:amazon:webservices and it should work :)
1. Create an ELB or ALB pointing HTTPS publicly to HTTP 8080 on your local server
    1. Ideally you can use the ACM service to generate/maintain the cert to terminate encryption
    1. For bonus points you can create an IIS site on 80 that redirects / to https://idp.mydomain.com/idp/profile/SAML2/Unsolicited/SSO?providerId=urn:amazon:webservices and then two ALB listener rules - one that sends / to 80 and everything else to 8080 on the backend
        1. That means you can go to https://idp.mydomain.com and it'll get you to the right place
