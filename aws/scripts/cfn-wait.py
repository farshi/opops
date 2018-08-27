#!/usr/bin/python
import sys
import time
import argparse
import boto3
import botocore

cfn = None
elb = None
args = None

def parse_args():
    """
    Parse command line arguments
    """
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', "--stack", action='store',
        default="", dest='stack', help= 'stack name')
    parser.add_argument('-t', "--timeout", action='store', default=1800,
            type=int, dest='timeout', help= 'timeout, default: 1800')
    parser.add_argument('-q', "--quiet", action='store', default=False,
            type=int, dest='quiet', help= 'quiet stdout output')
    args = parser.parse_args()

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
            elb = boto3.client('elb')
        except Exception as e:
            print e
            sys.exit(1)
    return elb 

def wait_cfn(stackname, timeout=1800):
    """
    wait cloudformation finish
    """
    cfn = getcfn()
    start_time = int(time.time())
    ret = 0
    now = None
    while True:
        if now:
            time.sleep(15)
        response = {}
        info("Checking CFN: %s" % stackname)
        try:
            response = cfn.describe_stacks(StackName=stackname)
        except Exception as e:
            print e
            sys.exit(1)

        now = int(time.time())
        if (now - start_time) > timeout:
            print "CloudFormation status checking timeout"
            ret = 3
            break
        stacks = response.get("Stacks", [])
        if len(stacks) != 1:
            print "Error: failed parse cloudformation stack"
            sys.exit(1)
        stack = stacks[0]
        info("Status: %s" % stack["StackStatus"])
        if stack["StackStatus"] == "CREATE_COMPLETE":
            ret = 0
            break
        if stack["StackStatus"] == "CREATE_FAILED":
            ret = 2
            break
    return ret

def info(msg):
    if not args.quiet:
        print msg
        sys.stdout.flush()

def wait_elb(stackname, timeout=300):
    """
    Wait ELB to become healthy
    This function parse a cloudformation stack, find out all elb resources
    and wait till all ELB to become healthy.
    Return 0 if all ELB become healthy before timeout
    otherwise return 1
    """
    cfn = getcfn()
    response = cfn.describe_stack_resources(StackName=stackname)
    resources = response["StackResources"]
    elbs = [ r for r in resources if r["ResourceType"] == "AWS::ElasticLoadBalancing::LoadBalancer" ]

    start_time = int(time.time())
    allinservice = False 
    while True:
        now = int(time.time())
        if (now - start_time) > timeout:
            print "ELB health check failed with timeout"
            break
        allinservice = True 
        for elb in elbs:
            elb_name = elb["PhysicalResourceId"]
            if not args.quiet:
                print "Checking ELB: %s" % elb_name
            client = getelb()
            response = client.describe_instance_health(LoadBalancerName=elb_name)
            instances = response["InstanceStates"]
            if len(instances) == 0:
                info("No registered instance")
                allinservice = False
            atleastone = False
            for instance in instances:
                info("Instance: %s State: %s" % (instance["InstanceId"], instance["State"]))
                if instance["State"] == "InService":
                    atleastone = True
            if atleastone is False:
                allinservice = False
        if allinservice is True:
            break
        time.sleep(15)

    if allinservice:
        return 0
    else:
        return 1

if __name__ == '__main__':
    parse_args()
    ret = 0
    if args.stack:
        ret = wait_cfn(args.stack, timeout=args.timeout)
        info("") 
        if ret == 0:
            ret = wait_elb(args.stack, timeout=args.timeout)
    sys.exit(ret)
