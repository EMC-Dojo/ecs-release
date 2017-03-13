#!/var/vcap/packages/python_2.7.13/bin/python

"""
This module provisions a new user and a storage pool and uploads a license
 - only runs if instance 0
 - only runs if user is not defined
 - only runs if no license is uploaded
 - only runs if storagepool is not defined
"""

import sys
import os
import time
import subprocess
import re
import json

# sys.path.insert(0, "/var/vcap/packages/ecs_community_edition/ecs-multi-node/")
# import step2_object_provisioning as CORE

INSTANCEID = sys.argv[1]
USERNAME = "root"
PASSWORD = "ChangeMe"

print "--- Parsed Configuration ---"
print "Instance: %s" % INSTANCEID
print "Username: %s" % USERNAME
print "Password: %s" % PASSWORD

def check_users(ecs_node, user, password):
    """
    Check to see if root still has not changed password.
    """
    try:
        curlCommand = "curl -i -k https://%s:4443/login -u %s:%s" % (ecs_node, user, password)
        print ("Checking User: %s " % curlCommand)
        res=subprocess.check_output(curlCommand, shell=True)
        failedTokenPattern = "Access is denied due to invalid or expired credentials"
        searchObject=re.search(failedTokenPattern,res)
        assert searchObject == None
    except Exception as ex:
        print "Username/Password already changed! Bailing out."
        sys.exit(0)

def poll_auth_service(ecs_node, user, password):
    """
    Poll to see if Auth Service is active.
    """
    print "Waiting on Authentication Service. This may take several minutes."
    for _ in range(0, 60):
        time.sleep(30)
        curl_command = "curl -i -k https://%s:4443/login -u %s:%s" % (ecs_node, user, password)
        print "Executing getAuthToken: %s " % curl_command
        res = subprocess.check_output(curl_command, shell=True)
        if re.search("X-SDS-AUTH-TOKEN:(.*)\r\n", res):
            return
        if re.search("HTTP/1.1 401 Unauthorized\r\n", res):
            sys.exit(0)
        print "Authentication service not yet started, retrying again...."
    print "Auth Service Never Started..."
    sys.exit(1)

def get_auth_token(ecs_node, user, password):
    curl_command = "curl -i -k https://%s:4443/login -u %s:%s" % (ecs_node, user, password)
    print "Executing getAuthToken: %s " % curl_command
    res = subprocess.check_output(curl_command, shell=True)
    auth_token_pattern = "X-SDS-AUTH-TOKEN:(.*)\r\n"
    search_object = re.search(auth_token_pattern, res)
    assert search_object, "Get Auth Token failed"
    print "Auth Token %s" % search_object.group(1)
    return search_object.group(1)

def execute_rest_API(url, method, filter, data, ECSNode, auth_tok, contentType='json',checkOutput=0):
    if data:
        subprocess.call("echo %s > request_body.tmp" % data, shell=True)
        data="-d @request_body.tmp"
    if "license" in url:
        data="-T license.lic"
    curlCommand = "curl -s -k -X %s -H 'Content-Type:application/%s' \
    -H 'X-SDS-AUTH-TOKEN:%s' \
    -H 'ACCEPT:application/%s' \
    %s https://%s:4443%s" %(method, contentType, auth_tok, contentType,data, ECSNode, url)
    print ("Executing REST API command: %s " % curlCommand)
    if checkOutput:
        jsonResult = subprocess.check_output(curlCommand, shell=True)
        RestOutputDict = {}
        RestOutputDict = json.loads(jsonResult)
        return RestOutputDict
        assert "code" not in jsonResult, "%s %s failed" % (method, url)
    else:
        res = subprocess.check_output(curlCommand, shell=True)
        print res
def check_license(ecs_node, user, password):
    license_json = execute_rest_API("/license", 'GET', '', '', "localhost",
                                    get_auth_token(ecs_node, user, password), 'xml', 1)
    if license_json['license_feature'][0]['notice'].contains("ACTIVATED TO"):
        print "License already loaded"
        sys.exit(0)
def check_instance(instanceid):
    if instanceid != "0":
        print "This post-deploy script only runs on instance 0"
        sys.exit(0)

    if poll_auth_service("localhost", "root", "ChangeMe"):
        print "Error polling auth service"

def check_storage_pool(ecs_node, user, password):
    storage_pool_json = execute_rest_API("/vdc/data-services/varrays.json", 'GET', '', '',
                                         "localhost", get_auth_token(ecs_node, user, password),
                                         checkOutput=1)
    for storage_pool in storage_pool_json[0]['varray']:
        if storage_pool["name"] == "bosh":
            sys.exit(0)
    create_storage_pool(ecs_node, user, password)



def create_storage_pool(ecs_node, user, password):
    storage_pool = "bosh"
    print "\nCreate Storage Pool %s" % storage_pool
    storage_pool_payload = '{\\"name\\":\\"%s\\",\
    \\"description\\":\\"%s\\",\
    \\"isProtected\\":\\"%s\\",\
    \\"isColdStorageEnabled\\":\\"%s\\"\
    }' % (storage_pool, "Storage Pool for BOSH", "false", "false")
    execute_rest_API("/vdc/data-services/varrays", 'POST', '.id', storage_pool_payload,
                     "localhost", get_auth_token(ecs_node, user, password), checkOutput=1)
    print "Storage Pool %s was created" % storage_pool

check_instance(INSTANCEID)
poll_auth_service("localhost", USERNAME, PASSWORD)
check_license("localhost", USERNAME, PASSWORD)
check_storage_pool("localhost", USERNAME, PASSWORD)
