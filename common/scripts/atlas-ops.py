#!/usr/bin/python
from functools import wraps
import os
import sys
import time
import argparse
import requests
import urllib2
import socket
import httplib
import time

 

def parse_args():
    """
    Parse command line arguments
    """
    global args
    parser = argparse.ArgumentParser()
    parser.add_argument('-H', "--health", action='store_true',
        default=False, dest='health', help= 'health check for app')

    parser.add_argument('-url', "--url", action='store', 
            default="", dest='url', help= 'URL')

    args = parser.parse_args()


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


@retry(Exception, tries=4, delay=40, backoff=2)
def check_url( url , timeout=5 ):
    healthy = False
    return  urllib2.urlopen(url,timeout=timeout).getcode() == 200 
              


def main():
    parse_args()
    ret = 0   
    if args.health:
        app_healthy=False
        app_url="http://"+args.url+"/atlasoperate/api/v1/health"
        summary_url="http://"+args.url+"/atlasoperate/api/operate-server-build-summary"
        try:
            check_url(app_url)
            app_healthy=True
        except Exception as e:
            app_healthy = False
        except socket.timeout as e:
            app_healthy = False
        
        if app_healthy :
            print ("App is running and healthy ... " )
            print ("URL : " + summary_url + "\n")
            f = requests.get(summary_url)
            print f.text  
        else:
            print ("Lookslike App is Not Healthy!!!!" )
        ret=app_healthy
    sys.exit(ret)

if __name__ == '__main__':
    main()
