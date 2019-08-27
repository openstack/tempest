# Copyright 2018 ZTE Corporation.  All rights reserved.
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

property_info = {
    'type': 'object',
    'properties': {
        'type': {'type': 'string'},
        'description': {'type': 'string'},
        'title': {'type': 'string'}
    },
    'additionalProperties': False,
    'required': ['type', 'description', 'title']
}

show_backend_capabilities = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'pool_name': {'type': ['string', 'null']},
            'description': {'type': ['string', 'null']},
            'volume_backend_name': {'type': 'string'},
            'namespace': {'type': 'string',
                          'pattern': '^OS::Storage::Capabilities::.+$'},
            'visibility': {'type': ['string', 'null']},
            'driver_version': {'type': 'string'},
            'vendor_name': {'type': 'string'},
            'properties': {
                'type': 'object',
                'properties': {
                    '^.+$': property_info
                },
            },
            'storage_protocol': {'type': 'string'},
            'replication_targets': {'type': 'array'},
            'display_name': {'type': ['string', 'null']}
        },
        'additionalProperties': False,
        'required': ['pool_name', 'volume_backend_name', 'namespace',
                     'visibility', 'driver_version', 'vendor_name',
                     'properties', 'storage_protocol', 'replication_targets',
                     'display_name', 'description']
    }
}
