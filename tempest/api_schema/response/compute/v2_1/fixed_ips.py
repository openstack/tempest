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

get_fixed_ip = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'fixed_ip': {
                'type': 'object',
                'properties': {
                    'address': {
                        'type': 'string',
                        'format': 'ip-address'
                    },
                    'cidr': {'type': 'string'},
                    'host': {'type': 'string'},
                    'hostname': {'type': 'string'}
                },
                'required': ['address', 'cidr', 'host', 'hostname']
            }
        },
        'required': ['fixed_ip']
    }
}

reserve_fixed_ip = {
    'status_code': [202],
    'response_body': {'type': 'string'}
}
