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

list_flavors = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'flavors': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'links': parameter_types.links,
                        'id': {'type': 'string'}
                    },
                    'required': ['name', 'links', 'id']
                }
            }
        },
        'required': ['flavors']
    }
}

common_flavor_info = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'links': parameter_types.links,
        'ram': {'type': 'integer'},
        'vcpus': {'type': 'integer'},
        'swap': {'type': 'integer'},
        'disk': {'type': 'integer'},
        'id': {'type': 'string'}
    },
    'required': ['name', 'links', 'ram', 'vcpus',
                 'swap', 'disk', 'id']
}

common_flavor_list_details = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'flavors': {
                'type': 'array',
                'items': common_flavor_info
            }
        },
        'required': ['flavors']
    }
}

common_flavor_details = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'flavor': common_flavor_info
        },
        'required': ['flavor']
    }
}
