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

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

common_floating_ip_info = {
    'type': 'object',
    'properties': {
        # NOTE: Now the type of 'id' is integer, but
        # here allows 'string' also because we will be
        # able to change it to 'uuid' in the future.
        'id': {'type': ['integer', 'string']},
        'pool': {'type': ['string', 'null']},
        'instance_id': {'type': ['string', 'null']},
        'ip': parameter_types.ip_address,
        'fixed_ip': parameter_types.ip_address
    },
    'additionalProperties': False,
    'required': ['id', 'pool', 'instance_id',
                 'ip', 'fixed_ip'],

}
list_floating_ips = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'floating_ips': {
                'type': 'array',
                'items': common_floating_ip_info
            },
        },
        'additionalProperties': False,
        'required': ['floating_ips'],
    }
}

create_get_floating_ip = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'floating_ip': common_floating_ip_info
        },
        'additionalProperties': False,
        'required': ['floating_ip'],
    }
}

add_remove_floating_ip = {
    'status_code': [202]
}
