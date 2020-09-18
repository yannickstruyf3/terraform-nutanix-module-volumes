#!/usr/bin/python
"""
Manages volume group creation and deletion.
Also attaches clients to volume groups based on IP or IQN
Input states:
    - create
    - delete
Input json keys:
    - "volume_name": Name of the volume to be managed
    - "volume_size_mb": Size of the volume
    - "storage_container_uuid": ID of the storage container
    - "volume_retain_on_destroy": Keep the volume and only detach the clients
    - "client_addresses": List of clients that need access to the volume. Format:  "client_addresses":[{ "client_address" : "10.10.10.10" }]
Environment variables:
    - "PE_USERNAME": Prism Element username
    - "PE_PASSWORD": Prism Element password
    - "PE_IP_ADDR": Prism Element IP

Example: manage_volumes.py create '"{"storage_container_uuid":"id","volume_name":"yst-vol","volume_retain_on_destroy":0,"volume_size_mb":"10240"}"
"""
import json
import os
import sys

import requests
from requests.auth import HTTPBasicAuth


def get_base_url(data):
    """Returns the base API url for volume groups"""
    return "https://%s:9440/api/nutanix/v2.0/volume_groups" % __get_param(data, "pe")


def __get_param(data, key):
    """Gets a parameters from the input json and checks if the value is set"""
    val = data.get(key)
    if not val:
        raise Exception("value for key {} was None in JSON data".format(key))
    return val


def __get_env_value(key):
    """Retrieves a value from the environment variables."""
    val = os.getenv(key)
    if not val:
        raise Exception("environment variable %s must be set!" % key)
    return val


def get_basic_auth(data):
    """Returns a HTTPBasicAuth objects used for API calls"""
    return HTTPBasicAuth(__get_param(data, "pe_user"), __get_param(data, "pe_pw"))


def parse_http_resonse(response):
    """Checks the HTTP response codes."""
    status_code = response.status_code
    if status_code < 200 or status_code > 299:
        raise Exception(
            "Request to failed with status code {}. Error: {}".format(
                status_code, response.text
            )
        )
    response_json = response.json()
    return response_json


def create_volume_group(data):
    """Creates a volume group. Volume group data is extracted from input json"""
    payload = {
        "name": __get_param(data, "volume_name"),
        "description": "",
        "enabled_authentications": [{"auth_type": "none", "password": ""}],
        "flash_mode_enabled": False,
        "attached_clients": __parse_attached_clients(data),
        "is_shared": True,
        "iscsi_target_prefix": __get_param(data, "volume_name"),
        "disk_list": [
            {
                "create_spec": {
                    "container_uuid": __get_param(data, "storage_container_uuid"),
                    "size_mb": int(__get_param(data, "volume_size_mb")),
                }
            }
        ],
    }
    resp = requests.post(
        get_base_url(data), auth=get_basic_auth(data), verify=False, json=payload
    )
    parse_http_resonse(resp)


def get_all_volume_groups(data):
    """Gets all of the volume groups in Prism Element"""
    resp = requests.get(get_base_url(data), auth=get_basic_auth(data), verify=False)
    parsed_response = parse_http_resonse(resp)
    entities = parsed_response.get("entities")
    if not entities:
        raise Exception("get_all_volume_groups did not return entities!")
    return entities


def get_volume_group(data):
    """
    Gets a volume groups from Prism Element.
    volume_name parameter must be passed in the input json.
    """
    volume_groups = get_all_volume_groups(data)
    volume_group_name = __get_param(data, "volume_name")
    for vol in volume_groups:
        if vol.get("name") == volume_group_name:
            return vol
    return None


def detach_all_from_vg(volume_group, data):
    """Detaches all clients from a volume group"""
    attached_clients = volume_group.get("attachment_list", [])
    if len(attached_clients) == 0:
        print("No attached clients, skipping detaching")
        return
    volume_group["attached_clients"] = []
    del volume_group["iscsi_target"]
    uuid = __get_volume_group_uuid(volume_group)
    put_url = "%s/%s" % (get_base_url(data), uuid)
    resp = requests.put(
        put_url, auth=get_basic_auth(data), verify=False, json=volume_group
    )
    parse_http_resonse(resp)
    print("Detached clients")


def attach_to_vg(volume_group, data):
    """Attaches the clients passed in the input json to the volume group"""
    volume_group["attached_clients"] = __parse_attached_clients(data)
    del volume_group["iscsi_target"]
    uuid = __get_volume_group_uuid(volume_group)
    put_url = "%s/%s" % (get_base_url(data), uuid)
    resp = requests.put(
        put_url, auth=get_basic_auth(data), verify=False, json=volume_group
    )
    parse_http_resonse(resp)


def delete_volume_group(volume_group_uuid, data):
    """Deletes a volume group. Volume group name is extracted from input json"""
    volume_retain_on_destroy = data.get("volume_retain_on_destroy", 0)
    if int(volume_retain_on_destroy) == 1:
        print("volume_retain_on_destroy was set to 1. Not destroying")
        return
    delete_url = "%s/%s" % (get_base_url(data), volume_group_uuid)
    resp = requests.delete(delete_url, auth=get_basic_auth(data), verify=False)
    parse_http_resonse(resp)
    print("Deleted volume group")


def __parse_attached_clients(data):
    """Parses the client_addresses attribute passed in the input json."""
    client_addresses = data.get("client_addresses", [])
    client_addreses_result = []
    for c_element in client_addresses:
        client_address = c_element.get("client_address")
        if not client_address:
            raise Exception("Each client address must have the 'client_address' key")
        client_addreses_result.append(
            {
                "client_address": client_address,
                "enabled_authentications": [{"auth_type": "NONE", "password": None}],
            }
        )
    return client_addreses_result


def __get_volume_group_uuid(volume_group):
    """Retrieves the UUID from a volume group."""
    uuid = volume_group.get("uuid")
    if not uuid:
        raise Exception("Unable to fetch uuid from volume group")
    return uuid


##main
if len(sys.argv) != 3:
    raise Exception("Require following inputs:\n- task\n json")

task = sys.argv[1]
if task not in ["create", "delete"]:
    raise Exception("task input must be create or delete")

input_json_str = sys.argv[2]
try:
    input_json = json.loads(input_json_str)
except Exception as exc:
    raise Exception("Invalid json passed as second argument") from exc

input_json["pe_user"] = __get_env_value("PE_USERNAME")
input_json["pe_pw"] = __get_env_value("PE_PASSWORD")
input_json["pe"] = __get_env_value("PE_IP_ADDR")
print("Connecting to PE %s with user %s" % (input_json["pe"], input_json["pe_user"]))
existing_vol = get_volume_group(input_json)
if task == "create":
    if existing_vol:
        print("volume group already exists. Skipping...")
        print("attaching to vg")
        attach_to_vg(existing_vol, input_json)
    else:
        create_volume_group(input_json)
        print("Created volume group")
if task == "delete":
    if existing_vol:
        detach_all_from_vg(existing_vol, input_json)
        delete_volume_group(__get_volume_group_uuid(existing_vol), input_json)
    else:
        print("Volume group doesn't exist, skipping...")
