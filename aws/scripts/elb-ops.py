#!/usr/bin/python
from functools import wraps
import os
import sys
import time
import argparse
import boto3
import botocore
import requests
import urllib2
import socket

import time

cfn = None
elb = None
args = None
r53 = None



def parse_args():
    """
    Parse command line arguments
    """
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', "--health", action='store_true',
        default=False, dest='health', help= 'health check for ELB')

    parser.add_argument('-G', "--green", action='store_true',
        default=False, dest='green', help= 'green')
    parser.add_argument('-D', "--decomission", action='store_true',
        default=False, dest='decomission', help= 'decomission')
    parser.add_argument('-s', "--stack", action='store',
        default="", dest='stack', help= 'stack name')

    parser.add_argument('-F', "--force", action='store_true',
        default=False, dest='force', help= 'Force delete stack')
    parser.add_argument('-b', "--buildnumber", action='store',
        default="0", dest='build_number', help= 'build number')

    parser.add_argument('-d', "--domain", action='store', 
            default="", dest='domain', help= 'DNS')
    parser.add_argument('-q', "--quiet", action='store', default=False,
            type=int, dest='quiet', help= 'quiet stdout output')
    args = parser.parse_args()
    if not args.domain.endswith("."):
        args.domain = args.domain + "."


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    def deco_retry(f):

        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry


def error(func):
    def dec():
        try:
            func()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                print "No such entity"
            elif e.response['Error']['Code'] == "AccessDenied":
                print "Access denied, please check credentials"
                sys.exit(1)
        except Exception,e:
            print 'Error: %s' % e 
            sys.exit(1)
            #raise e 
    return dec

def getcfn():
    global cfn 
    if not cfn: 
        try: 
            cfn = boto3.client('cloudformation')
        except Exception as e:
            print e
            sys.exit(1)
    return cfn 

def getelb():
    global elb 
    if not elb: 
        try: 
            elb = boto3.client('elbv2')
        except Exception as e:
            print e
            sys.exit(1)
    return elb 

def getr53():
    global r53 
    if not r53: 
        try: 
            r53 = boto3.client('route53')
        except Exception as e:
            print e
            sys.exit(1)
    return r53 

def find_stack(stackname):
    """
    find cloudformation stack 
    """
    cfn = getcfn()
    ret = 0
    now = None
    response = {}
    info("Checking CFN: %s" % stackname)
    try:
        response = cfn.list_stacks()
    except Exception as e:
        print e
        sys.exit(1)
    stacks = response["StackSummaries"]
    stackname = ""
    for stack in stacks:
        if stack["StackStatus"] == "DELETE_COMPLETE":
            continue
        if not stack["StackName"].startswith(args.stack):
            continue
        if not stack["StackName"].endswith("-%s" % args.build_number):
            continue
        stackname = stack["StackName"]
        break
    if not stackname:
        return
    print "Found: %s" % stackname
    return stackname

def delete_stack(stackname):
    """
    delete cloudformation stack 
    """
    cfn = getcfn()
    now = None
    ret = 0
    response = {}
    try:
        response = cfn.delete_stack(StackName=stackname)
        print "Deleting stack: %s" % stackname
    except Exception as e:
        print e
        ret = 1
    return ret

def info(msg):
    if not args.quiet:
        print msg

def find_elb_dns_names(stackname):
    """
    This function parse a cloudformation stack, find out all elb resources
    and return DNS Name(list) of the all ELBs
    """
    cname = ""
    cfn = getcfn()
    response = cfn.describe_stack_resources(StackName=stackname)
    resources = response["StackResources"]
    elbs = [ r for r in resources if r["ResourceType"] == "AWS::ElasticLoadBalancingV2::LoadBalancer" ]
    elb_names = [ e["PhysicalResourceId"] for e in elbs ]
    if not args.quiet:
        print "Checking ELB: %s" % elb_names 
    client = getelb()
    response = client.describe_load_balancers(LoadBalancerArns=elb_names)
    descs = response["LoadBalancers"]
    dns_names = {}
    for desc in descs:
        if desc.has_key("CanonicalHostedZoneId"):
            dns_names[desc["DNSName"]] = desc["CanonicalHostedZoneId"]
    print "ELB DNS URL: %s" % desc["DNSName"]
    return dns_names

def get_r53_hostedzone_id():
    r53 = getr53()
    response = r53.list_hosted_zones()
    hostedzones = response["HostedZones"]
    hostedzone_id = None
    for hostedzone in hostedzones:
        tmp = hostedzone["Name"].strip(".")
        if tmp in args.domain:
            hostedzone_id = hostedzone["Id"]
            hostedzone_name = hostedzone["Name"]
            break
    if not hostedzone_id:
        print "Error: Could not find hosted zone"
        return
    return hostedzone_id

def get_r53_record_set(hostedzone_id):
    r53 = getr53()
    response = r53.list_resource_record_sets(HostedZoneId=hostedzone_id)
    record_sets = response["ResourceRecordSets"]
    ret = []
    for record_set in record_sets:
        if record_set["Type"] != "A":
            continue
        if not record_set.get("AliasTarget", None):
            continue
        ret.append(record_set)
    print ret
    return ret 

@retry(urllib2.URLError, tries=4, delay=30, backoff=2)
def check_url( url , timeout=5 ):
    healthy = False
    return  urllib2.urlopen(url,timeout=timeout).getcode() == 200        


def check_domain(domain, elb_dns_names):
    """
    Check if the domain is pointed to ELB
    """
    ret = False
    if domain == "":
        return ret 
    print "Checking DNS: %s" % domain
    ret = False
    hostedzone_id = get_r53_hostedzone_id()
    if not hostedzone_id:
        return ret
    records = get_r53_record_set(hostedzone_id)
    for record in records:
        for elb_dns_name in elb_dns_names.keys():
            print "elb_dns_name " , elb_dns_name 
            if elb_dns_name.lower() in record["AliasTarget"]["DNSName"].lower():
                print "%s --> %s" % (record["Name"], elb_dns_name)
                ret = True
                break
        if ret is True:
            break
    return ret

def update_domain(hostedzone_id, domain, elb_hostedzone_id, elb_dns_name):
    """
    Update Roue53 record to ELB
    """
    alias_target = {u'HostedZoneId': elb_hostedzone_id, u'EvaluateTargetHealth': False, u'DNSName': elb_dns_name}
    resource_record_set = { "Name": domain, "Type": "A", "AliasTarget": alias_target }
    changes = [{ "Action": "UPSERT", "ResourceRecordSet": resource_record_set }]
    change_batch = { "Comment": "Comment", "Changes": changes }
    print change_batch


    r53 = getr53()
    print "hostedzone_id", hostedzone_id
    r53.change_resource_record_sets(HostedZoneId=hostedzone_id, ChangeBatch = change_batch)

def main():
    parse_args()
    build_number = os.getenv("buildNumber", None)
    ret = 0
    print args.stack
    if build_number:
        args.build_number = build_number

    while True:
        if args.decomission:
            stackname = find_stack(args.stack)
            if not stackname:
                print "Error: Stack not found"
                ret = 1
                break
            elb_dns_names = find_elb_dns_names(stackname)
            if check_domain(args.domain, elb_dns_names) and args.force is False:
                print "Warning: Stack in use, will not delete the stack"
            else:
                ret = delete_stack(stackname)
            break

        if args.green:
            stackname = find_stack(args.stack)
            if not stackname:
                print "Error: Stack not found"
                ret = 1
                break
            elb_hostedzone_ids = find_elb_dns_names(stackname)
            elb_dns_name = elb_hostedzone_ids.keys()[0]
            hostedzone_id = get_r53_hostedzone_id()
            update_domain(hostedzone_id, args.domain, elb_hostedzone_ids[elb_dns_name], elb_dns_name)
            break
        if args.health:
            app_healthy=False
            stackname = find_stack(args.stack)
            if not stackname:
                print "Error: Stack not found"
                ret = 1
                break
            elb_hostedzone_ids = find_elb_dns_names(stackname)
            elb_dns_name = elb_hostedzone_ids.keys()[0]
            app_url="http://"+elb_dns_name+"/atlasoperate/api/v1/health"
            summary_url="http://"+elb_dns_name+"/atlasoperate/api/operate-server-build-summary"
            try:
                check_url(app_url)
                app_healthy=True
            except urllib2.URLError as e:
                app_healthy = False
            except socket.timeout as e:
                app_healthy = False
          
            if app_healthy :
                print ("App is running and healthy ... " )
                print ("URL : " + summary_url + "\n")
                f = requests.get(summary_url)
                print f.text  
            else:
                print ("App is Not Healthy!!! , please investigate logs on splunk !" )
            ret=app_healthy
            break
        break
    sys.exit(ret)

if __name__ == '__main__':
    main()
