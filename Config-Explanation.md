# shibboleth3-aws-duo-config-explanation
Explanation for the config and its changes from defaults

1. mfa-authn-config.xml
    1. Set this up this so that it validates the Password then moves on to Duo as a 2nd factor
1. attribute-filter.xml - allow the necessary parameters to do the AWS federation
1. attribute-resolver.xml
    1. AWS requires two attributes to be returned to it:
        1. awsRoleSessionName - we map this to the email from AD/LDAP
        1. awsRoles - this is the AWS role ID(s) that you can assume
            1. It bases this on membership of AD groups that start with AWS- and assumes there is a corresponding role called Shibboleth-. For example AWS-Admins in AD = Shibboleth-Admins in AWS
1. idp.properties
    1. The two main changes from the defaults are:
        1. Setting idp.authn.flows to MFA flow (this flow is Password then MFA)
        1. idp.encryption.optional needs to be true to work with AWS
1. ldap.properties
    1. The changes from the defaults are:
        1. useStartTLS and useSSL set to false (required for talking to Simple AD but you might need these on for other directories)
        1. bindDNCredential the installer seems to mess up the case so double-check it
        1. The searchFilter needs to be set to (sAMAccountName=$resolutionContext.principal)
1. metadata-providers.xml
    1. Set this to pull from https://signin.aws.amazon.com/static/saml-metadata.xml
1. relying-party.xml
    1. Remove the p:postAuthenticationFlows="attribute-release" from the lines to disable the consent confirmation prompts
1. jetty-base/start.d/idp.ini
    1. nonhttps.host change to 0.0.0.0 to allow it to be reached outside of the server
    1. nonhttps.port change to 8080 to allow for an IIS or nginx to redirect / to the login URI
1. Jetty/etc/jetty.xml
    1. In order to have a Load balancer in front of it you need to add
    `<Call name="addCustomizer">
        <Arg><New class="org.eclipse.jetty.server.ForwardedRequestCustomizer"/></Arg>
    </Call>`