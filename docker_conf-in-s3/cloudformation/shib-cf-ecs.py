# Troposphere to create CloudFormation template of Shibboleth ECS Deployment
# By Jason Umiker (jason.umiker@gmail.com)

from troposphere import Parameter, Ref, Template
from troposphere.ecs import (
    Service, TaskDefinition, ContainerDefinition, PortMapping, LoadBalancer, Environment
)

t = Template()
t.add_version('2010-09-09')

cluster = t.add_parameter(Parameter(
    'Cluster',
    Type='String',
    Description='The ECS Cluster to deploy to.',
))

s3path = t.add_parameter(Parameter(
    'S3PATH',
    Type='String',
    Description='The path to the config tarball in S3',
))

shibboleth_image = t.add_parameter(Parameter(
    'ShibbolethImage',
    Type='String',
    Description='The Shibboleth container image to deploy.',
))

redirect_image = t.add_parameter(Parameter(
    'RedirectImage',
    Type='String',
    Description='The Redirect container image to deploy.',
))

task_role_arn = t.add_parameter(Parameter(
    'TaskRoleARN',
    Type='String',
    Description='The ARN of the role for the task.',
))

shibboleth_lb_target_arn = t.add_parameter(Parameter(
    'ShibLBTargetARN',
    Type='String',
    Description='The ARN of the ALB Target Group for Shibboleth.',
))

redirect_lb_target_arn = t.add_parameter(Parameter(
    'RedirectLBTargetARN',
    Type='String',
    Description='The ARN of the ALB Target Group for the redirect.',
))



shibboleth_task_definition = t.add_resource(TaskDefinition(
    'ShibbolethTaskDefinition',
    TaskRoleArn=Ref(task_role_arn),
    ContainerDefinitions=[
        ContainerDefinition(
            Name='shibboleth',
            Image=Ref(shibboleth_image),
            MemoryReservation=1024,
            Essential=True,
            PortMappings=[PortMapping(ContainerPort=8080)],
            Environment=[
                Environment(
                    Name='S3PATH',
                    Value=Ref(s3path)
                )
            ]
        )
    ]
))

shibboleth_service = t.add_resource(Service(
    'ShibbolethService',
    Cluster=Ref(cluster),
    DesiredCount=1,
    TaskDefinition=Ref(shibboleth_task_definition),
    LoadBalancers=[
        LoadBalancer(
            ContainerName='shibboleth',
            ContainerPort=8080,
            TargetGroupArn=Ref(shibboleth_lb_target_arn)
        )
    ]
))

redirect_task_definition = t.add_resource(TaskDefinition(
    'RedirectTaskDefinition',
    ContainerDefinitions=[
        ContainerDefinition(
            Name='shibboleth-redirect',
            Image=Ref(redirect_image),
            MemoryReservation=256,
            Essential=True,
            PortMappings=[PortMapping(ContainerPort=80)],
        )
    ]
))

redirect_service = t.add_resource(Service(
    'RedirectService',
    Cluster=Ref(cluster),
    DesiredCount=1,
    TaskDefinition=Ref(redirect_task_definition),
    LoadBalancers=[
        LoadBalancer(
            ContainerName='shibboleth-redirect',
            ContainerPort=80,
            TargetGroupArn=Ref(redirect_lb_target_arn)
        )
    ]
))

print(t.to_json())