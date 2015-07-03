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

common_agent_info = {
    'type': 'object',
    'properties': {
        'agent_id': {'type': ['integer', 'string']},
        'hypervisor': {'type': 'string'},
        'os': {'type': 'string'},
        'architecture': {'type': 'string'},
        'version': {'type': 'string'},
        'url': {'type': 'string', 'format': 'uri'},
        'md5hash': {'type': 'string'}
    },
    'additionalProperties': False,
    'required': ['agent_id', 'hypervisor', 'os', 'architecture',
                 'version', 'url', 'md5hash']
}

list_agents = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'agents': {
                'type': 'array',
                'items': common_agent_info
            }
        },
        'additionalProperties': False,
        'required': ['agents']
    }
}

create_agent = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'agent': common_agent_info
        },
        'additionalProperties': False,
        'required': ['agent']
    }
}

delete_agent = {
    'status_code': [200]
}
