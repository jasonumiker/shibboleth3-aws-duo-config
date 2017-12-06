# Troposphere to create CloudFormation template of Shibboleth ECS Deployment
# By Jason Umiker (jason.umiker@gmail.com)

from troposphere import Parameter, Ref, Template
from troposphere.ecs import (
    Service, TaskDefinition, ContainerDefinition, PortMapping, LoadBalancer
)

t = Template()
t.add_version('2010-09-09')

cluster = t.add_parameter(Parameter(
    'Cluster',
    Type='String',
    Description='The ECS Cluster to deploy to.',
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

shibboleth_task_definition = t.add_resource(TaskDefinition(
    'ShibbolethTaskDefinition',
    Cpu='1024',
    Memory='1024',
    ContainerDefinitions=[
        ContainerDefinition(
            Name='shibboleth',
            Image=Ref(shibboleth_image),
            Essential=True,
            PortMappings=[PortMapping(ContainerPort=8080)]
        )
    ]
))

shibboleth_service = t.add_resource(Service(
    'ShibbolethService',
    Cluster=Ref(cluster),
    DesiredCount=1,
    TaskDefinition=Ref(shibboleth_task_definition)

))

redirect_task_definition = t.add_resource(TaskDefinition(
    'RedirectTaskDefinition',
    Cpu='1024',
    Memory='512',
    TaskRoleArn=Ref(task_role_arn),
    ContainerDefinitions=[
        ContainerDefinition(
            Name='shibboleth-redirect',
            Image=Ref(redirect_image),
            Essential=True,
            PortMappings=[PortMapping(ContainerPort=80)]
        )
    ]
))

redirect_service = t.add_resource(Service(
    'RedirectService',
    Cluster=Ref(cluster),
    DesiredCount=1,
    TaskDefinition=Ref(redirect_task_definition)
))

print(t.to_json())