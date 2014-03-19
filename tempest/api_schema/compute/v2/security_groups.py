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

list_security_groups = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'security_groups': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': ['integer', 'string']},
                        'name': {'type': 'string'},
                        'tenant_id': {'type': 'string'},
                        'rules': {'type': 'array'},
                        'description': {'type': 'string'},
                    },
                    'required': ['id', 'name', 'tenant_id', 'rules',
                                 'description'],
                }
            }
        },
        'required': ['security_groups']
    }
}
