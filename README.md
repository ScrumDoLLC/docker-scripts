# docker-scripts
A set of scripts we use with Docker and Amazon ECS/ECR to manage things.


# update-tasks.py

This is part of our continuous integration environment to deploy changes.

This script will register a new version of an ECS task definition so it can be used to update a service in our docker cluster.

It copies all settings from the most recent task definition, and sets a new image.

To make it work, we tag our images with a version number in the docker registry in the format of v## (ex. v10 or v100)  (We grab the build number form circle-ci's environment variable representing the build number.)

You should set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY env variables.  Optional to set AWS_EC2_REGION (defaults to us-east-1)

```
usage: update-tasks.py [-h] [--tag TAG] [--tasks TASKS [TASKS ...]]
                       [--images IMAGES [IMAGES ...]]

Register new versions of container images in tasks.

optional arguments:
  -h, --help            show this help message and exit
  --tag TAG             Docker tag of new version of images
  --tasks TASKS [TASKS ...] ECS Task Definitions to update
  --images IMAGES [IMAGES ...] Container images to update within the tasks

```                        

Example:

python update-tasks.py --task web celery --images scrumdo-web --tag v248

This would upgrade two tasks, web and celery.  Inside those tasks, it would set any container using the scrumdo-web image
to use the one tagged v248

NOTE: This script does not update any services, so you have to either push a button or run another script to actually do the deployment.
