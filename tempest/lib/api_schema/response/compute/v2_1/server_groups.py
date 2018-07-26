# Copyright 2017 NTT Corporation.  All rights reserved.
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

common_server_group = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'name': {'type': 'string'},
        'policies': {
            'type': 'array',
            'items': {'type': 'string'}
        },
        # 'members' attribute contains the array of instance's UUID of
        # instances present in server group
        'members': {
            'type': 'array',
            'items': {'type': 'string'}
        },
        'metadata': {'type': 'object'}
    },
    'additionalProperties': False,
    'required': ['id', 'name', 'policies', 'members', 'metadata']
}

create_show_server_group = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server_group': common_server_group
        },
        'additionalProperties': False,
        'required': ['server_group']
    }
}

delete_server_group = {
    'status_code': [204]
}

list_server_groups = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server_groups': {
                'type': 'array',
                'items': common_server_group
            }
        },
        'additionalProperties': False,
        'required': ['server_groups']
    }
}
