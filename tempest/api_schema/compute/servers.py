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

get_password = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'password': {'type': 'string'}
        },
        'required': ['password']
    }
}

get_vnc_console = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'console': {
                'type': 'object',
                'properties': {
                    'type': {'type': 'string'},
                    'url': {
                        'type': 'string',
                        'format': 'uri'
                    }
                },
                'required': ['type', 'url']
            }
        },
        'required': ['console']
    }
}

delete_server = {
    'status_code': [204],
}

set_server_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'metadata': {'type': 'object'}
        },
        'required': ['metadata']
    }
}

list_server_metadata = copy.deepcopy(set_server_metadata)
