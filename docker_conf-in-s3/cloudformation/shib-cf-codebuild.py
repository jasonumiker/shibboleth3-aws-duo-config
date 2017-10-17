# Troposphere to create CloudFormation template of Shibboleth CodeBuild
# and base dependencies for Shibboleth IdP container image and config
# By Jason Umiker (jason.umiker@gmail.com)

from troposphere import Output, Join, Ref, Template, Parameter
from troposphere import AWS_ACCOUNT_ID, AWS_REGION
from troposphere import ecr, s3, iam, codebuild

t = Template()

t.add_description("Template to deploy a Dockerised Shibboleth IdP "
                  "Build Environment")

# Get the required Parameters
idp_hostname = t.add_parameter(Parameter(
    "hostname",
    Description="FQDN of the IdP (idp.example.com)",
    Type="String"
))

idp_attributescope = t.add_parameter(Parameter(
    "attributescope",
    Description="Domain Name of the AD (ad.example.com)",
    Type="String"
))

idp_ldapURL = t.add_parameter(Parameter(
    "ldapURL",
    Description="LDAP connection string (ldap://ad.example.com:389)",
    Type="String"
))

idp_ldapbaseDN = t.add_parameter(Parameter(
    "idpldapbaseDN",
    Description="LDAP root path where users live (\"CN=Users, DC=ad, DC=example, DC=com\")",
    Type="String"
))

idp_ldapbindDN = t.add_parameter(Parameter(
    "ldapbindDN",
    Description="Username to log into LDAP (shib_svc@ad.example.com)",
    Type="String"
))

idp_ldapdnFormat = t.add_parameter(Parameter(
    "ldapdnFormat",
    Description="How to convert username to fully qualified name (%s@ad.example.com)",
    Type="String"
))

idp_duo_apiHost = t.add_parameter(Parameter(
    "duoapiHost",
    Description="API endpoint location from Duo",
    Type="String"
))

idp_duo_integrationKey = t.add_parameter(Parameter(
    "duointegrationKey",
    Description="Integration Key from Duo",
    Type="String"
))

# Create the ECR Repository
ECRepository = t.add_resource(
    ecr.Repository(
        'Repository'
    )
)

# Create the S3 Bucket for the Configuration
S3Bucket = t.add_resource(
    s3.Bucket(
        'ConfigBucket'
    )
)

# Create instance/task roles
# Instance Role
InstanceRole = t.add_resource(iam.Role(
    "InstanceRole",
    AssumeRolePolicyDocument={
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'Service': ['ec2.amazonaws.com']},
            'Action': ["sts:AssumeRole"]
        }],
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'Service': 'codebuild.amazonaws.com'},
            "Action": "sts:AssumeRole"
        }]
    },
))

# Task Role
TaskRole = t.add_resource(iam.Role(
    "TaskRole",
    AssumeRolePolicyDocument={
        'Statement': [{
            'Effect': 'Allow',
            'Principal': {'Service': ['ecs-tasks.amazonaws.com']},
            'Action': ["sts:AssumeRole"]
        }]},
))

# Create the Policies and associate them with the above roles
# Policy to read/write to the ECR Repository
ECRAccessPolicy = t.add_resource(iam.PolicyType(
    'ECRAccessPolicy',
    PolicyName='shibboleth-ecr',
    PolicyDocument={'Version': '2012-10-17',
                    'Statement': [{'Action': ['ecr:GetAuthorizationToken'],
                                   'Resource': ['*'],
                                   'Effect': 'Allow'},
                                  {'Action': ['ecr:*'],
                                   'Resource': [
                                       Join("", ["arn:aws:ecr:",
                                                 Ref(AWS_REGION),
                                                 ":", Ref(AWS_ACCOUNT_ID),
                                                 ":repository/",
                                                 Ref(ECRepository)]
                                            ),
                                   ],
                                   'Effect': 'Allow'},
                                  ]},
    Roles=[Ref(InstanceRole), Ref(TaskRole)],
))

# Policy to read/write to the config S3 bucket
S3AccessPolicy = t.add_resource(iam.PolicyType(
    'S3AccessPolicy',
    PolicyName='shibboleth-s3',
    PolicyDocument={'Version': '2012-10-17',
                    'Statement': [{'Action': ['s3:Get*', 's3:List*', 's3:PutObject',
                                              's3:DeleteObject'],
                                   'Resource': [
                                       Join("", ["arn:aws:s3:::", Ref(S3Bucket), "/*"]),
                                   ],
                                   'Effect': 'Allow'},
                                  ]},
    Roles=[Ref(InstanceRole), Ref(TaskRole)],
))

# Policy to read/write from the PS'
PSAccessPolicy = t.add_resource(iam.PolicyType(
    'PSAccessPolicy',
    PolicyName='shibboelth-ps',
    PolicyDocument={'Version': '2012-10-17',
                    'Statement': [{'Action': ['ssm:GetParameters', 'ssm:PutParameter',
                                              'ssm:DescribeParameters'],
                                   'Resource': ['arn:aws:ssm:*:*:parameter/shibboleth/*'],
                                   'Effect': 'Allow'
                                   },
                                  ]},
    Roles=[Ref(InstanceRole), Ref(TaskRole)],
))

# CodeBuild Service Policy
CodeBuildServiceRolePolicy = t.add_resource(iam.PolicyType(
    'CodeBuildServiceRolePolicy',
    PolicyName='CodeBuildServiceRolePolicy',
    PolicyDocument={"Version": "2012-10-17",
                    "Statement": [
                        {
                            "Sid": "CloudWatchLogsPolicy",
                            "Effect": "Allow",
                            "Action": [
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents"
                            ],
                            "Resource": [
                                "*"
                            ]
                        },
                        {
                            "Sid": "CodeCommitPolicy",
                            "Effect": "Allow",
                            "Action": [
                                "codecommit:GitPull"
                            ],
                            "Resource": [
                                "*"
                            ]
                        },
                        {
                            "Sid": "S3GetObjectPolicy",
                            "Effect": "Allow",
                            "Action": [
                                "s3:GetObject",
                                "s3:GetObjectVersion"
                            ],
                            "Resource": [
                                "*"
                            ]
                        },
                        {
                            "Sid": "S3PutObjectPolicy",
                            "Effect": "Allow",
                            "Action": [
                                "s3:PutObject"
                            ],
                            "Resource": [
                                "*"
                            ]
                        }
                    ]},
    Roles=[Ref(InstanceRole)],
))

# Create CodeBuild Projects
# Image Build
ImageArtifacts = codebuild.Artifacts(Type='NO_ARTIFACTS')

ImageEnvironment = codebuild.Environment(
    ComputeType='BUILD_GENERAL1_SMALL',
    Image='aws/codebuild/docker:1.12.1',
    Type='LINUX_CONTAINER',
    EnvironmentVariables=[{'Name': 'AWS_DEFAULT_REGION', 'Value': 'ap-southeast-2'},
                          {'Name': 'AWS_ACCOUNT_ID', 'Value': Ref(AWS_ACCOUNT_ID)},
                          {'Name': 'IMAGE_REPO_NAME', 'Value': Ref(ECRepository)},
                          {'Name': 'IMAGE_TAG', 'Value': 'latest'}],
    PrivilegedMode=True
)

ImageSource = codebuild.Source(
    Location='https://github.com/jasonumiker/shibboleth3-aws-duo-config',
    Type='GITHUB'
)

ImageProject = codebuild.Project(
    "ImageBuildProject",
    Artifacts=ImageArtifacts,
    Environment=ImageEnvironment,
    Name='shibboleth-build',
    ServiceRole=Ref(InstanceRole),
    Source=ImageSource,
    DependsOn=CodeBuildServiceRolePolicy
)
t.add_resource(ImageProject)

# Config Build
ConfigArtifacts = codebuild.Artifacts(Type='NO_ARTIFACTS')

ConfigEnvironment = codebuild.Environment(
    ComputeType='BUILD_GENERAL1_SMALL',
    Image='aws/codebuild/docker:1.12.1',
    Type='LINUX_CONTAINER',
    EnvironmentVariables=[{'Name': 'idp_hostname', 'Value': Ref(idp_hostname)},
                          {'Name': 'idp_attributescope', 'Value': Ref(idp_attributescope)},
                          {'Name': 'idp_ldapURL', 'Value': Ref(idp_ldapURL)},
                          {'Name': 'idp_ldapbaseDN', 'Value': Ref(idp_ldapbaseDN)},
                          {'Name': 'idp_ldapbindDN', 'Value': Ref(idp_ldapbindDN)},
                          {'Name': 'idp_ldapdnFormat', 'Value': Ref(idp_ldapdnFormat)},
                          {'Name': 'idp_duo_apiHost', 'Value': Ref(idp_duo_apiHost)},
                          {'Name': 'idp_duo_integrationKey', 'Value': Ref(idp_duo_integrationKey)},
                          {'Name': 's3path', 'Value': Ref(S3Bucket)},
                          {'Name': 'awsregion', 'Value': Ref(AWS_REGION)}],
    PrivilegedMode=True
)

ConfigSource = codebuild.Source(
    Location='https://github.com/jasonumiker/shibboleth3-aws-duo-config',
    Type='GITHUB',
    BuildSpec='buildspec_conf.yml'
)

ConfigProject = codebuild.Project(
    "ConfigBuildProject",
    Artifacts=ConfigArtifacts,
    Environment=ConfigEnvironment,
    Name='shibboleth-config-build',
    ServiceRole=Ref(InstanceRole),
    Source=ConfigSource,
)
t.add_resource(ConfigProject)

# Output ECR repository URL
t.add_output(Output(
    "RepositoryURL",
    Description="The docker repository URL",
    Value=Join("", [
        Ref(AWS_ACCOUNT_ID),
        ".dkr.ecr.",
        Ref(AWS_REGION),
        ".amazonaws.com/",
        Ref(ECRepository)
    ]),
))

# Output the s3 bucket name
t.add_output(Output(
    "ShibbolethConfigBucketName",
    Value=Ref(S3Bucket),
    Description="Name of S3 bucket to hold Shibboleth Config"
))

print(t.to_json())
