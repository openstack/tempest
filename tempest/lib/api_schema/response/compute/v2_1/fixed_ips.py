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

get_fixed_ip = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'fixed_ip': {
                'type': 'object',
                'properties': {
                    'address': parameter_types.ip_address,
                    'cidr': {'type': 'string'},
                    'host': {'type': 'string'},
                    'hostname': {'type': 'string'}
                },
                'additionalProperties': False,
                'required': ['address', 'cidr', 'host', 'hostname']
            }
        },
        'additionalProperties': False,
        'required': ['fixed_ip']
    }
}

reserve_unreserve_fixed_ip = {
    'status_code': [202]
}
