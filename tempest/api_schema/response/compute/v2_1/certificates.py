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

_common_schema = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'certificate': {
                'type': 'object',
                'properties': {
                    'data': {'type': 'string'},
                    'private_key': {'type': 'string'},
                },
                'required': ['data', 'private_key']
            }
        },
        'required': ['certificate']
    }
}

get_certificate = copy.deepcopy(_common_schema)
get_certificate['response_body']['properties']['certificate'][
    'properties']['private_key'].update({'type': 'null'})

create_certificate = copy.deepcopy(_common_schema)
