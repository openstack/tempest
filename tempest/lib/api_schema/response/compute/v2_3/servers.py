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

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types
from tempest.lib.api_schema.response.compute.v2_1 import servers

# Compute microversion 2.3:
# 1. New attributes in 'os-extended-volumes:volumes_attached' dict.
#      'delete_on_termination'
# 2. New attributes in 'server' dict.
#      'OS-EXT-SRV-ATTR:reservation_id'
#      'OS-EXT-SRV-ATTR:launch_index'
#      'OS-EXT-SRV-ATTR:kernel_id'
#      'OS-EXT-SRV-ATTR:ramdisk_id'
#      'OS-EXT-SRV-ATTR:hostname'
#      'OS-EXT-SRV-ATTR:root_device_name'
#      'OS-EXT-SRV-ATTR:user_data'

server_detail = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'name': {'type': 'string'},
        'status': {'type': 'string'},
        'image': {'oneOf': [
            {'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'links': parameter_types.links
                },
                'additionalProperties': False,
                'required': ['id', 'links']},
            {'type': ['string', 'null']}
        ]},
        'flavor': {
            'type': 'object',
            'properties': {
                'id': {'type': 'string'},
                'links': parameter_types.links
            },
            'additionalProperties': False,
            'required': ['id', 'links']
        },
        'fault': {
            'type': 'object',
            'properties': {
                'code': {'type': 'integer'},
                'created': {'type': 'string'},
                'message': {'type': 'string'},
                'details': {'type': 'string'},
            },
            'additionalProperties': False,
            # NOTE(gmann): 'details' is not necessary to be present
            #  in the 'fault'. So it is not defined as 'required'.
            'required': ['code', 'created', 'message']
        },
        'user_id': {'type': 'string'},
        'tenant_id': {'type': 'string'},
        'created': {'type': 'string'},
        'updated': {'type': 'string'},
        'progress': {'type': 'integer'},
        'metadata': {'type': 'object'},
        'links': parameter_types.links,
        'addresses': parameter_types.addresses,
        'hostId': {'type': 'string'},
        'OS-DCF:diskConfig': {'type': 'string'},
        'accessIPv4': parameter_types.access_ip_v4,
        'accessIPv6': parameter_types.access_ip_v6,
        'key_name': {'type': ['string', 'null']},
        'security_groups': {'type': 'array'},
        'OS-SRV-USG:launched_at': {'type': ['string', 'null']},
        'OS-SRV-USG:terminated_at': {'type': ['string', 'null']},
        'OS-EXT-AZ:availability_zone': {'type': 'string'},
        'OS-EXT-STS:task_state': {'type': ['string', 'null']},
        'OS-EXT-STS:vm_state': {'type': 'string'},
        'OS-EXT-STS:power_state': parameter_types.power_state,
        'OS-EXT-SRV-ATTR:host': {'type': ['string', 'null']},
        'OS-EXT-SRV-ATTR:instance_name': {'type': 'string'},
        'OS-EXT-SRV-ATTR:hypervisor_hostname': {'type': ['string', 'null']},
        'config_drive': {'type': 'string'},
        # NOTE(gmann): new attributes in version 2.3
        'os-extended-volumes:volumes_attached': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'delete_on_termination': {'type': 'boolean'}
                },
                'additionalProperties': False,
            },
        },
        'OS-EXT-SRV-ATTR:reservation_id': {'type': ['string', 'null']},
        'OS-EXT-SRV-ATTR:launch_index': {'type': 'integer'},
        'OS-EXT-SRV-ATTR:kernel_id': {'type': ['string', 'null']},
        'OS-EXT-SRV-ATTR:ramdisk_id': {'type': ['string', 'null']},
        'OS-EXT-SRV-ATTR:hostname': {'type': 'string'},
        'OS-EXT-SRV-ATTR:root_device_name': {'type': ['string', 'null']},
        'OS-EXT-SRV-ATTR:user_data': {'type': ['string', 'null']},
    },
    'additionalProperties': False,
    # NOTE(gmann): 'progress' attribute is present in the response
    # only when server's status is one of the progress statuses
    # ("ACTIVE","BUILD", "REBUILD", "RESIZE","VERIFY_RESIZE")
    # 'fault' attribute is present in the response
    # only when server's status is one of the  "ERROR", "DELETED".
    # OS-DCF:diskConfig and accessIPv4/v6 are API
    # extensions, and some environments return a response
    # without these attributes.So these are not defined as 'required'.
    'required': ['id', 'name', 'status', 'image', 'flavor',
                 'user_id', 'tenant_id', 'created', 'updated',
                 'metadata', 'links', 'addresses', 'hostId']
}

server_detail['properties']['addresses']['patternProperties'][
    '^[a-zA-Z0-9-_.]+$']['items']['properties'].update({
        'OS-EXT-IPS:type': {'type': 'string'},
        'OS-EXT-IPS-MAC:mac_addr': parameter_types.mac_address})
# NOTE(gmann): Update OS-EXT-IPS:type and OS-EXT-IPS-MAC:mac_addr
# attributes in server address. Those are API extension,
# and some environments return a response without
# these attributes. So they are not 'required'.

get_server = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server': server_detail
        },
        'additionalProperties': False,
        'required': ['server']
    }
}

list_servers_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'servers': {
                'type': 'array',
                'items': server_detail
            },
            'servers_links': parameter_types.links
        },
        'additionalProperties': False,
        # NOTE(gmann): servers_links attribute is not necessary to be
        # present always So it is not 'required'.
        'required': ['servers']
    }
}

# NOTE: Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.1 ***
list_servers = copy.deepcopy(servers.list_servers)
update_server = copy.deepcopy(servers.update_server)
rebuild_server = copy.deepcopy(servers.rebuild_server)
rebuild_server_with_admin_pass = copy.deepcopy(
    servers.rebuild_server_with_admin_pass)
show_server_diagnostics = copy.deepcopy(servers.show_server_diagnostics)
attach_volume = copy.deepcopy(servers.attach_volume)
show_volume_attachment = copy.deepcopy(servers.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers.list_volume_attachments)
