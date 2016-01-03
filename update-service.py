#!/usr/bin/python
#
# This is part of our continous integration environment to deploy changes.
#
# This script will take an ECS service, look up any updated task definitions for the
# task, and update the service with the new version of the task definitions which will
# cause ECS to go through it's deploy process.
#
# After performing the update, this script will wait up to 10 minutes for the deployment
# to finish.

import argparse
import boto3
import sys
import os
import pprint
import re
import time

pp = pprint.PrettyPrinter(indent=4)


def connect_ecs(region=None):
    return boto3.client(
        'ecs',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=region or os.environ.get('AWS_EC2_REGION', 'us-east-1'),
    )

def update_service():
    parser = argparse.ArgumentParser(description='Register new versions of task definitions in a service.')
    parser.add_argument('--cluster', required=True, dest='cluster', help='ECS cluster to work on')
    parser.add_argument('--service', required=True, dest='service', help='Service to update')
    args = parser.parse_args()

    service_name = args.service
    cluster = args.cluster
    print("Updating service %s" % service_name)

    conn = connect_ecs()
    services = conn.describe_services(cluster=cluster, services=[service_name])['services']
    # pp.pprint(services)

    if len(services) != 1:
        raise Exception("Error: Unexpected number of services found")

    service = services[0]
    # del service['events']
    # pp.pprint(service)

    taskName = service['taskDefinition']

    match = re.search("task-definition\/(.+):([0-9]+)", taskName)
    if match is None:
        raise Exception("Error: Could not find task definition in service.")

    taskFamilyPrefix = match.group(1)
    taskVersion = match.group(2)

    print "Current task: %s version %s" % (taskFamilyPrefix, taskVersion)

    taskDefs = conn.list_task_definitions(familyPrefix=taskFamilyPrefix, status='ACTIVE', sort='DESC')
    targetTaskDef = taskDefs['taskDefinitionArns'][0]
    print "Target task: %s" % targetTaskDef

    res = conn.update_service(cluster=cluster, service=service_name, taskDefinition=targetTaskDef)
    # pp.pprint(res)

    c = 0
    while c < 120:  # only wait around for ~10 minutes (120 * 5 seconds)
        c += 1
        service = conn.describe_services(cluster=cluster, services=[service_name])['services'][0]
        if len(service['deployments']) ==1 and service['deployments'][0]['runningCount'] == service['deployments'][0]['desiredCount']:
            print "All done"
            return

        for deployment in service['deployments']:            
            print "%s %d/%d" % (deployment['taskDefinition'], deployment['runningCount'], deployment['desiredCount'])

        print ""
        time.sleep(5)

    raise Exception("Operation timed out")


if __name__ == "__main__":
    update_service()
    sys.stdout.flush()
