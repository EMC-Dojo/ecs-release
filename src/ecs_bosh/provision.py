#!/var/vcap/packages/python_2.7.13/bin/python

"""
This module does everything needed to utilize the ECS CloudFoundry Service Broker
 - only runs if the default user credentials were not changed
 - only runs if no license is uploaded
 - only runs if storagepool is not defined
"""

import sys
import os
import time
import subprocess
import re
import json


NODE0 = sys.argv[1]
NODE1 = sys.argv[2]
NODE2 = sys.argv[3]
USERNAME = "root"
PASSWORD = "ChangeMe"
STORAGE_POOL = "bosh"
VIRTUAL_DATA_CENTER = "bosh_vdc"
REPLICATION_GROUP = "bosh_rep_grp"
NAMESPACE = "bosh_namespace"
ALL_NODES = [NODE0, NODE1, NODE2]
ECS_MGT = sys.argv[4]
VERBOSE = False
if len(sys.argv) > 5:
    VERBOSE = True

if VERBOSE:
    print "--- Parsed Configuration ---"
    print "Username: %s" % USERNAME
    print "Password: %s" % PASSWORD
    print "ECS API endpoint: %s" % ECS_MGT
    print "ECS Node 0: %s" % NODE0
    print "ECS Node 1: %s" % NODE1
    print "ECS Node 2: %s" % NODE2
    print "ECS Storage Pool: %s" % STORAGE_POOL
    print "ECS Virtual Data Center: %s" % VIRTUAL_DATA_CENTER
    print "ECS Replication Group: %s" % REPLICATION_GROUP
    print "ECS Namespace: %s" % NAMESPACE

def poll_auth_service(ecs_node, user, password):
    """
    Poll to see if Auth Service is active.
    """
    if VERBOSE:
        print "_______________________________________"
        print "--| Ensuring the Auth Service is up |--"
        print "_______________________________________"

    res = ""
    auth_fault=0
    for _ in range(0, 60):
        time.sleep(30)
        curl_command = "curl -i -k https://%s:4443/login -u %s:%s" % (ecs_node, user, password)
        if VERBOSE:
            print "Getting an Auth Token: %s " % curl_command
        try:
            res = subprocess.check_output(curl_command, shell=True)
        except Exception as ex:
            if VERBOSE:
                print "Authentication service not yet started, retrying again...."
        if re.search("X-SDS-AUTH-TOKEN:(.*)\r\n", res):
            if VERBOSE:
                print "Token Success!"
            return
        if re.search("HTTP/1.1 401 Unauthorized\r\n", res):
            if auth_fault > 0:
                if VERBOSE:
                    print "Username & Password already changed from defaults!"
                sys.exit(0)
            else:
                auth_fault += 1
    if VERBOSE:
        print "Auth Service Never Started..."
    sys.exit(1)

def get_auth_token(ecs_node, user, password):
    curl_command = "curl -i -k https://%s:4443/login -u %s:%s" % (ecs_node, user, password)
    if VERBOSE:
        print "Executing getAuthToken: %s " % curl_command
    res = subprocess.check_output(curl_command, shell=True)
    auth_token_pattern = "X-SDS-AUTH-TOKEN:(.*)\r\n"
    search_object = re.search(auth_token_pattern, res)
    assert search_object, "Get Auth Token failed"
    if VERBOSE:
        print "Auth Token %s" % search_object.group(1)
    return search_object.group(1)

def execute_rest_API(url, method, filter, data, ECSNode, auth_tok, contentType='json',checkOutput=0):
    if data:
        subprocess.call("echo %s > request_body.tmp" % data, shell=True)
        data = "-d @request_body.tmp"
    if "license" in url:
        data = "-T license.lic"
    curlCommand = "curl -s -k -X %s -H 'Content-Type:application/%s' \
    -H 'X-SDS-AUTH-TOKEN:%s' \
    -H 'ACCEPT:application/%s' \
    %s https://%s:4443%s" %(method, contentType, auth_tok, contentType, data, ECSNode, url)
    if VERBOSE:
        print "Executing REST API command: %s " % curlCommand
    if checkOutput:
        jsonResult = subprocess.check_output(curlCommand, shell=True)
        RestOutputDict = {}
        RestOutputDict = json.loads(jsonResult)
        return RestOutputDict
    else:
        res = subprocess.check_output(curlCommand, shell=True)
        if VERBOSE:
            print res
        return

def check_license(ecs_node, user, password):
    if VERBOSE:
        print "___________________________________"
        print "--| Checking Status of License  |--"
        print "___________________________________"
    os.system("cp /var/vcap/packages/ecs_community_edition/ecs-multi-node/license.lic .")
    license_json = execute_rest_API("/license", 'GET', '', '', ecs_node,
                                    get_auth_token(ecs_node, user, password), checkOutput=1)
    if license_json['license_text'] == "The product is not licensed":
        if VERBOSE:
            print "Need to load license!"
        load_license(ecs_node, user, password)
    else:
        if VERBOSE:
            print "The product is already licensed"

def load_license(ecs_node, user, password):
    if VERBOSE:
        print "___________________________________"
        print "--| Loading Open Source License |--"
        print "___________________________________"
    execute_rest_API("/license", 'POST', '', '', ecs_node,
                     get_auth_token(ecs_node, user, password), contentType='xml')
    return

def check_storage_pool(ecs_node, user, password, storage_pool):
    if VERBOSE:
        print "___________________________________"
        print "--|   Checking Storage Pools    |--"
        print "___________________________________"
    storage_pool_json = execute_rest_API("/vdc/data-services/varrays.json", 'GET', '', '',
                                         ecs_node, get_auth_token(ecs_node, user, password),
                                         checkOutput=1)
    for prov_storage_pool in storage_pool_json['varray']:
        if prov_storage_pool['name'] == storage_pool:
            if VERBOSE:
                print "Skipping create, Storage Pool %s found!" % storage_pool
            return prov_storage_pool['id']
    if VERBOSE:
        print "Storage Pool %s not found." % storage_pool
    return create_storage_pool(ecs_node, user, password, storage_pool)

def create_storage_pool(ecs_node, user, password, storage_pool):
    if VERBOSE:
        print "_______________________________________"
        print "--|   Creating %s Storage Pool    |--" % storage_pool
        print "_______________________________________"
    storage_pool_payload = '{\\"name\\":\\"%s\\",\
    \\"description\\":\\"%s\\",\
    \\"isProtected\\":\\"%s\\",\
    \\"isColdStorageEnabled\\":\\"%s\\"\
    }' % (storage_pool, "Storage Pool for BOSH", "false", "false")
    storage_pool_resp = execute_rest_API("/vdc/data-services/varrays", 'POST', '',
                                         storage_pool_payload, ecs_node,
                                         get_auth_token(ecs_node, user, password), checkOutput=1)
    storage_pool_id = storage_pool_resp['id']
    if VERBOSE:
        print "Storage Pool %s was created with id %s" % (storage_pool, storage_pool_id)
    return storage_pool_id

def check_data_nodes(ecs_node, user, password, nodes, storage_pool_id):
    all_prov_nodes = execute_rest_API("/vdc/data-stores.json", 'GET', '', '',
                                      ecs_node, get_auth_token(ecs_node, user, password),
                                      checkOutput=1)
    for node in nodes:
        if VERBOSE:
            print "Checking if node %s is already provisioned" % node
        if node not in [x['id'] for x in all_prov_nodes['data_store']]:
            provision_node(ecs_node, user, password, node, storage_pool_id)
        else:
            if VERBOSE:
                print "Node %s already Provisioned!" % node
    return

def provision_node(ecs_node, user, password, new_node, storage_pool_id):
    if VERBOSE:
        print "____________________________________________________________________"
        print "--|   Creating %s Node & Adding to %s Storage Pool    |--" % (new_node, storage_pool_id)
        print "--|       THIS CAN TAKE SOME TIME......GO GRAB A COFFEE          |--"
        print "____________________________________________________________________"
    create_node_payload = '{ \\"nodes\\":[\
    {\
    \\"nodeId\\":\\"%s\\",\\"name\\":\\"%s\\",\
    \\"virtual_array\\":\\"%s\\",\\"description\\":\\"%s\\"\
    }]}' % (new_node, new_node, storage_pool_id, "Datastore_for_bosh")
    execute_rest_API('/vdc/data-stores/commodity', 'POST', '', create_node_payload, ecs_node,
                     get_auth_token(ecs_node, user, password))
    return

def check_nodes_status(ecs_node, user, password, nodes):
    if VERBOSE:
        print "____________________________________________________"
        print "--|           Ensuring Nodes Are Ready           |--"
        print "--|   THIS CAN TAKE SOME TIME......PING PONG?    |--"
        print "____________________________________________________"

    for node in nodes:
        url = "/vdc/data-stores/commodity/%s" % node
        node_ready = 0
        while not node_ready:
            node_status = execute_rest_API(url, 'GET', '', '', ecs_node,
                                           get_auth_token(ecs_node, user, password), checkOutput=1)
            if node_status['device_state'] == "readytouse":
                if VERBOSE:
                    print "Node %s ready to use!" % node
                node_ready = 1
            else:
                time.sleep(60)
    return

def check_virtual_data_center(ecs_node, user, password, node, vdc):
    if VERBOSE:
        print "____________________________________________________"
        print "--|           Checking for BOSH VDC              |--"
        print "____________________________________________________"

    vdc_resp = execute_rest_API('/object/vdcs/vdc/%s' % vdc, 'GET', '', '', ecs_node,
                                get_auth_token(ecs_node, user, password), checkOutput=1)
    if 'code' in vdc_resp:
        return create_virtual_data_center(ecs_node, user, password, node, vdc)
    else:
        return vdc_resp['id']

def create_virtual_data_center(ecs_node, user, password, node, vdc):
    if VERBOSE:
        print "____________________________________________________"
        print "--|              Creating BOSH VDC               |--"
        print "____________________________________________________"

    if VERBOSE:
        print "Adding node %s to virtual data center %s!" % (node, vdc)
    secret_key = "secret12345"
    insert_vdc_payload = '{\\"vdcName\\":\\"%s\\",\
    \\"interVdcEndPoints\\":\\"%s\\", \
    \\"secretKeys\\":\\"%s\\"\
    }' % (vdc, node, secret_key)
    execute_rest_API('/object/vdcs/vdc/%s' % vdc, 'PUT', '', insert_vdc_payload,
                     ecs_node, get_auth_token(ecs_node, user, password))
    return check_virtual_data_center(ecs_node, user, password, node, vdc)

def check_replication_group(ecs_node, user, password, vdc, sp, group):
    if VERBOSE:
        print "____________________________________________________________"
        print "--|        Checking for BOSH Replication Group           |--"
        print "____________________________________________________________"

    rep_group_resp = execute_rest_API('/vdc/data-service/vpools', 'GET', '', '', ecs_node,
                                      get_auth_token(ecs_node, user, password), checkOutput=1)
    found = [x['id'] for x in rep_group_resp['data_service_vpool'] if group == x['name']]

    if found:
        return found[0]
    else:
        return create_replication_group(ecs_node, user, password, vdc, sp, group)

def create_replication_group(ecs_node, user, password, vdc, sp, group):
    if VERBOSE:
        print "____________________________________________________________"
        print "--|           Create BOSH Replication Group              |--"
        print "____________________________________________________________"

    rep_group_payload = '{\\"description\\":\\"%s\\",\
    \\"name\\":\\"%s\\", \
    \\"zone_mappings\\":[\
    {\
    \\"name\\":\\"%s\\",\\"value\\":\\"%s\\"\
    }]}' % (group, group, vdc, sp)

    rep_group_resp = execute_rest_API('/vdc/data-service/vpools', 'POST', '', rep_group_payload,
                                      ecs_node, get_auth_token(ecs_node, user, password),
                                      checkOutput=1)
    return rep_group_resp['id']

def check_namespace(ecs_node, user, password, rep_group, namespace):
    if VERBOSE:
        print "____________________________________________________________"
        print "--|             Checking for BOSH Namespace              |--"
        print "____________________________________________________________"

    namespace_resp = execute_rest_API('/object/namespaces', 'GET', '', '', ecs_node,
                                      get_auth_token(ecs_node, user, password), checkOutput=1)
    found = [x['id'] for x in namespace_resp['namespace'] if namespace == x['name']]

    if not found:
        create_namespace(ecs_node, user, password, rep_group, namespace)
    return

def create_namespace(ecs_node, user, password, rep_group, namespace):
    if VERBOSE:
        print "____________________________________________________________"
        print "--|               Create BOSH Namespace                  |--"
        print "____________________________________________________________"

    namespace_payload = '{\\"namespace\\": \\"%s\\",\
    \\"default_data_services_vpool\\": \\"%s\\"\
    }' % (namespace, rep_group)
    execute_rest_API("/object/namespaces/namespace", 'POST', '', namespace_payload, ecs_node,
                     get_auth_token(ecs_node, user, password))

poll_auth_service(ECS_MGT, USERNAME, PASSWORD)
check_license(ECS_MGT, USERNAME, PASSWORD)
SP_ID = check_storage_pool(ECS_MGT, USERNAME, PASSWORD, STORAGE_POOL)
check_data_nodes(ECS_MGT, USERNAME, PASSWORD, ALL_NODES, SP_ID)
check_nodes_status(ECS_MGT, USERNAME, PASSWORD, ALL_NODES)
VDC_ID = check_virtual_data_center(ECS_MGT, USERNAME, PASSWORD, ALL_NODES[0], VIRTUAL_DATA_CENTER)
RG_ID = check_replication_group(ECS_MGT, USERNAME, PASSWORD, VDC_ID, SP_ID, REPLICATION_GROUP)
check_namespace(ECS_MGT, USERNAME, PASSWORD, RG_ID, NAMESPACE)

print "HAVE FUN WITH ECS, WE SURE DID PUTTING THIS BOSH RELEASE TOGETHER! :D"
