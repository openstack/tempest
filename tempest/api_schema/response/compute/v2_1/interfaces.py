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

from tempest.api_schema.response.compute import parameter_types

interface_common_info = {
    'type': 'object',
    'properties': {
        'port_state': {'type': 'string'},
        'fixed_ips': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'subnet_id': {
                        'type': 'string',
                        'format': 'uuid'
                    },
                    'ip_address': {
                        'type': 'string',
                        'format': 'ipv4'
                    }
                },
                'required': ['subnet_id', 'ip_address']
            }
        },
        'port_id': {'type': 'string', 'format': 'uuid'},
        'net_id': {'type': 'string', 'format': 'uuid'},
        'mac_addr': parameter_types.mac_address
    },
    'required': ['port_state', 'fixed_ips', 'port_id', 'net_id', 'mac_addr']
}

get_create_interfaces = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'interfaceAttachment': interface_common_info
        },
        'required': ['interfaceAttachment']
    }
}

list_interfaces = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'interfaceAttachments': {
                'type': 'array',
                'items': interface_common_info
            }
        },
        'required': ['interfaceAttachments']
    }
}

delete_interface = {
    'status_code': [202]
}
