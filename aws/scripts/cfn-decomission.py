#!/usr/bin/python
#
# This script decomission a CloudFormation stack
#
import os
import sys
import time
import argparse
import boto3
import botocore

cfn = None
args = None

def parse_args():
    """
    Parse command line arguments
    """
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', "--stack", action='store',
        default="", dest='stack', help= 'stack name')
    parser.add_argument('-y', "--yes", action='store_true', 
            default=False, dest='yes', help= 'skip confirmation prompt')
    parser.add_argument('-t', "--timeout", action='store', default=1800,
            type=int, dest='timeout', help= 'timeout, default: 1800')
    parser.add_argument('-q', "--quiet", action='store', default=False,
            type=int, dest='quiet', help= 'quiet stdout output')
    args = parser.parse_args()
    if not args.stack:
        sys.exit(1)

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

def find_stack(stackname):
    """
    find cloudformation stack 
    """
    cfn = getcfn()
    ret = 0
    now = None
    response = {}
    info("Checking CloudFormation Stack: %s" % stackname)
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
        if stackname == "":
            stackname = stack["StackName"]
        elif len(stack["StackName"]) < len(stackname):
            stackname = stack["StackName"]
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

def wait_delete_complete(stackname, timeout=600):
    """
    wait stack delete to complete
    """
    cfn = getcfn()
    ret = 0
    now = None
    response = {}
    done = False 
    now = None
    start_time = int(time.time())
    print "Checking stack status: %s" % stackname
    while not done:
        if now:
            time.sleep(10)
        stacks = [] 
        next_token = None
        try:
            response = cfn.list_stacks()
        except Exception as e:
            print e
            sys.exit(1)
        stacks.extend(response["StackSummaries"])
        found = False 
        done = False
        failed = False
        for stack in stacks:
            if stack["StackName"] != stackname:
                continue
            found = True
            completed = True
            falied = False 
            info("Stack status: %s" % stack["StackStatus"])
            if stack["StackStatus"] == "DELETE_FAILED":
                print "Error: Delete stack failed"
                failed = True 
                break
            if stack["StackStatus"] != "DELETE_COMPLETE":
                completed = False 
                break
            if completed:
                done = True
                break
        
        if not found:
            print "stack not found"
            ret = 0
            break
        if failed == True:
            ret = 2
            break 
        if done:
            continue

        now = int(time.time())
        if (now - start_time) > timeout:
            print "CloudFormation status checking timeout"
            ret = 2
            break
    return ret 

def info(msg):
    if not args.quiet:
        print msg

def main():
    parse_args()
    ret = 0
    stackname = ""
    deleted = False 
    stackname = find_stack(args.stack)
    while stackname:
        if not args.yes:
            user_input = raw_input('Delete CloudFormation stack %s [Y/N]' % args.stack)
            if user_input not in ('Y','y','Yes','YES','yes'):
                ret = 1
                break 
            ret = delete_stack(stackname)
            deleted = True
        else:
            ret = delete_stack(stackname)
            deleted = True
        break
    if deleted:
        ret = wait_delete_complete(stackname)
    sys.exit(ret)

if __name__ == '__main__':
    main()
