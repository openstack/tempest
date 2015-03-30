# Copyright 2015 NEC Corporation.  All rights reserved.
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

param_network = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'cidr': {'type': ['string', 'null']},
        'label': {'type': 'string'}
    },
    'required': ['id', 'cidr', 'label']
}


list_tenant_networks = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'networks': {
                'type': 'array',
                'items': param_network
            }
        },
        'required': ['networks']
    }
}


get_tenant_network = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'network': param_network
        },
        'required': ['network']
    }
}
