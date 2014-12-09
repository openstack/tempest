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

list_services = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'services': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': ['integer', 'string'],
                               'pattern': '^[a-zA-Z!]*@[0-9]+$'},
                        'zone': {'type': 'string'},
                        'host': {'type': 'string'},
                        'state': {'type': 'string'},
                        'binary': {'type': 'string'},
                        'status': {'type': 'string'},
                        'updated_at': {'type': ['string', 'null']},
                        'disabled_reason': {'type': ['string', 'null']}
                    },
                    'required': ['id', 'zone', 'host', 'state', 'binary',
                                 'status', 'updated_at', 'disabled_reason']
                }
            }
        },
        'required': ['services']
    }
}

enable_service = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'service': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'binary': {'type': 'string'},
                    'host': {'type': 'string'}
                },
                'required': ['status', 'binary', 'host']
            }
        },
        'required': ['service']
    }
}
