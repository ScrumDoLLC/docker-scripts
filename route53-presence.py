#!/usr/bin/python
#
# Register the local EC2 instance with route53, replacing any existing record.

import argparse
import os
import time
import sys

import boto
from boto.route53.record import ResourceRecordSets
import requests

def get_zone_id(hostname):
  domainname = '.'.join(hostname.split('.')[-2:])
  zone = conn.get_hosted_zone_by_name(domainname)
  if not zone:
    print "Sorry, you don't have access to that domain!"
    exit(1)
  return zone.GetHostedZoneResponse.Id.split('/')[2]

def get_ip(local):
  if local:
    scope = 'local'
  else:
    scope = 'public'
  return requests.get("http://169.254.169.254/latest/meta-data/{}-ipv4".format(scope)).content

def register(hostname, ip, ttl):
  changes = ResourceRecordSets(conn, zone_id)
  change = changes.add_change('UPSERT', hostname, 'A', ttl)
  change.add_value(ip)
  return changes.commit()

parser = argparse.ArgumentParser(description='Register or unregister a name in Route53.')
parser.add_argument('hostname', help='fqdn to manipulate')
parser.add_argument('--ttl', default=600, help='ttl in seconds, default 600')
parser.add_argument('--local', action='store_true', help='use local IP instead of public')

args = parser.parse_args()

conn = boto.connect_route53(os.environ.get('AWS_ACCESS_KEY'), os.environ.get('AWS_SECRET_KEY'))
zone_id = get_zone_id(args.hostname)
print "Zone id: %s" % zone_id
result = register(args.hostname, get_ip(args.local), args.ttl)
if not result:
  print "Error"
  exit(1)
else:
  print "Registered {}: {}".format(args.hostname, result.ChangeResourceRecordSetsResponse.ChangeInfo.Status)
sys.stdout.flush()
