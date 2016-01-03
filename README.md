# docker-scripts
A set of scripts we use with Docker and Amazon ECS/ECR to manage things.


# update-tasks.py

This is part of our continuous integration environment to deploy changes.  We use this script in our build process after we
build, tag, and push our docker images.

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

# route53-presence.py

We run this script from inside a container in a startup script.  It sets a DNS lookup to itself, utilizing the EC2 meta-info to figure out it's own ip address.  This is a cheap and easy way to do service discovery, there are better ways since changing the host that
the service runs on could result in downtime equal to your TTL.

```
usage: route53-presence.py [-h] [--ttl TTL] [--local] hostname

Register or unregister a name in Route53.

positional arguments:
  hostname    fqdn to manipulate

optional arguments:
  -h, --help  show this help message and exit
  --ttl TTL   ttl in seconds, default 600
  --local     use local IP instead of public
```  


Example:

./route53-presence.py --ttl 60 --local myservice.domain.com

Registers our local/private (10.\*.\*.\*) address with route53 to the given hostname with a time to live of 60 seconds.

No copyright claimed on this script, original version of this script taken from: https://github.com/timelinelabs/docker-route53-presence
