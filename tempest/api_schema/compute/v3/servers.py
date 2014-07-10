# Copyright 2014 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import copy

from tempest.api_schema.compute import parameter_types
from tempest.api_schema.compute import servers

create_server = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'server': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'os-security-groups:security_groups': {'type': 'array'},
                    'links': parameter_types.links,
                    'admin_password': {'type': 'string'},
                    'os-access-ips:access_ip_v4': parameter_types.access_ip_v4,
                    'os-access-ips:access_ip_v6': parameter_types.access_ip_v6
                },
                # NOTE: os-access-ips:access_ip_v4/v6 are API extension,
                # and some environments return a response without these
                # attributes. So they are not 'required'.
                'required': ['id', 'os-security-groups:security_groups',
                             'links', 'admin_password']
            }
        },
        'required': ['server']
    }
}

addresses_v3 = copy.deepcopy(parameter_types.addresses)
addresses_v3['patternProperties']['^[a-zA-Z0-9-_.]+$']['items'][
    'properties'].update({
        'type': {'type': 'string'},
        'mac_addr': {'type': 'string'}
    })
addresses_v3['patternProperties']['^[a-zA-Z0-9-_.]+$']['items'][
    'required'].extend(
        ['type', 'mac_addr']
    )

update_server = copy.deepcopy(servers.base_update_get_server)
update_server['response_body']['properties']['server']['properties'].update({
    'addresses': addresses_v3,
    'host_id': {'type': 'string'},
    'os-access-ips:access_ip_v4': parameter_types.access_ip_v4,
    'os-access-ips:access_ip_v6': parameter_types.access_ip_v6
})
update_server['response_body']['properties']['server']['required'].append(
    # NOTE: os-access-ips:access_ip_v4/v6 are API extension,
    # and some environments return a response without these
    # attributes. So they are not 'required'.
    'host_id'
)

get_server = copy.deepcopy(servers.base_update_get_server)
get_server['response_body']['properties']['server']['properties'].update({
    'key_name': {'type': ['string', 'null']},
    'host_id': {'type': 'string'},

    # NOTE: Non-admin users also can see "os-server-usage" and
    # "os-extended-availability-zone" attributes.
    'os-server-usage:launched_at': {'type': ['string', 'null']},
    'os-server-usage:terminated_at': {'type': ['string', 'null']},
    'os-extended-availability-zone:availability_zone': {'type': 'string'},

    # NOTE: Admin users only can see "os-extended-status" and
    # "os-extended-server-attributes" attributes.
    'os-extended-status:task_state': {'type': ['string', 'null']},
    'os-extended-status:vm_state': {'type': 'string'},
    'os-extended-status:power_state': {'type': 'integer'},
    'os-extended-status:locked_by': {'type': ['string', 'null']},
    'os-extended-server-attributes:host': {'type': ['string', 'null']},
    'os-extended-server-attributes:instance_name': {'type': 'string'},
    'os-extended-server-attributes:hypervisor_hostname': {
        'type': ['string', 'null']
    },
    'os-extended-volumes:volumes_attached': {'type': 'array'},
    'os-pci:pci_devices': {'type': 'array'},
    'os-access-ips:access_ip_v4': parameter_types.access_ip_v4,
    'os-access-ips:access_ip_v6': parameter_types.access_ip_v6,
    'os-config-drive:config_drive': {'type': 'string'}
})
get_server['response_body']['properties']['server']['required'].append(
    # NOTE: os-server-usage, os-extended-availability-zone,
    # os-extended-status, os-extended-server-attributes,
    # os-extended-volumes, os-pci, os-access-ips and
    # os-config-driveare API extension, and some environments
    # return a response without these attributes. So they are not 'required'.
    'host_id'
)

attach_detach_volume = {
    'status_code': [202]
}

set_get_server_metadata_item = copy.deepcopy(servers.set_server_metadata)

list_addresses_by_network = {
    'status_code': [200],
    'response_body': addresses_v3
}

server_actions_change_password = copy.deepcopy(
    servers.server_actions_delete_password)

list_addresses = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'addresses': addresses_v3
        },
        'required': ['addresses']
    }
}

update_server_metadata = copy.deepcopy(servers.update_server_metadata)
# V3 API's response status_code is 201
update_server_metadata['status_code'] = [201]

server_actions_object = copy.deepcopy(servers.common_instance_actions)
server_actions_object['properties'].update({'server_uuid': {'type': 'string'}})
server_actions_object['required'].extend(['server_uuid'])

list_server_actions = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server_actions': {
                'type': 'array',
                'items': server_actions_object
            }
        },
        'required': ['server_actions']
    }
}
