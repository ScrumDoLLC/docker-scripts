#!/usr/bin/python
#
# This is part of our continous integration environment to deploy changes.
#
# This script will register a new version of an ECS task definition so it
# can be used to update a service in our docker cluster.
#
# It copies all settings from the most recent task definition, and sets a new image.
#
# To make it work, we tag our images with a version number in the docker registry
# in the format of v## (ex. v10 or v100)
# We grab the build number form circle-ci's environment variable representing the build number.
#
# You should set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables.
# Optional to set AWS_EC2_REGION (defaults to us-east-1)

import argparse
import os
import time
import sys
import pprint
import json
import re
pp = pprint.PrettyPrinter(indent=4)

import boto3


def connect_ecs(region=None):
    return boto3.client(
        'ecs',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=region or os.environ.get('AWS_EC2_REGION', 'us-east-1'),
    )

def update_tasks():
    parser = argparse.ArgumentParser(description='Register new versions of container images in tasks.')
    parser.add_argument('--tag', dest='tag', help='Docker tag of new version of images')
    parser.add_argument('--tasks', nargs='+', dest='tasks', help='ECS Task Definitions to update')
    parser.add_argument('--images', nargs='+', dest='images', help='Container images to update within the tasks')

    args = parser.parse_args()
    images = args.images
    tasks = args.tasks
    tag = args.tag

    print("Task definitions to update: {}".format(tasks))
    print("Container images to update: {}".format(images))
    print("Image tag to use: {}\n".format(tag))

    conn = connect_ecs()

    for task in tasks:
        print("Updating %s" % task)
        existing_definitions = conn.list_task_definitions(familyPrefix=task)
        last_definition = existing_definitions

        if len(last_definition['taskDefinitionArns']) == 0:
            raise Exception("No task definitions found in your account.")

        previous_arn = last_definition['taskDefinitionArns'][-1]
        print("Previous definition %s" % previous_arn)
        previous_def = conn.describe_task_definition(taskDefinition=previous_arn)
        task_def = previous_def['taskDefinition']

        for container in task_def["containerDefinitions"]:
            previous_image = container["image"]
            if len([True for i in images if i in previous_image]) == 0:
                # We only update container images listed in images, this way a single task can have
                # containers we do upgrade as well as containers we don't.
                print "Not updating %s" % previous_image
                continue
            new_image = re.sub("\:.*","",previous_image) + ":%s" % tag
            print "Upgrading image %s -> %s" % (previous_image, new_image)
            container["image"] = new_image

        l = [json.dumps(t) for t in task_def["containerDefinitions"]]
        result = conn.register_task_definition(family=task, containerDefinitions=task_def["containerDefinitions"])
        print "New task definition: %s" % result['taskDefinition']['taskDefinitionArn']
        print "Deregistering %s\n" % previous_arn
        conn.deregister_task_definition(taskDefinition=previous_arn)


if __name__ == "__main__":
    update_tasks()
    sys.stdout.flush()
