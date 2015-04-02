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

links = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'href': {
                'type': 'string',
                'format': 'uri'
            },
            'rel': {'type': 'string'}
        },
        'required': ['href', 'rel']
    }
}

mac_address = {
    'type': 'string',
    'pattern': '(?:[a-f0-9]{2}:){5}[a-f0-9]{2}'
}

access_ip_v4 = {
    'type': 'string',
    'anyOf': [{'format': 'ipv4'}, {'enum': ['']}]
}

access_ip_v6 = {
    'type': 'string',
    'anyOf': [{'format': 'ipv6'}, {'enum': ['']}]
}

addresses = {
    'type': 'object',
    'patternProperties': {
        # NOTE: Here is for 'private' or something.
        '^[a-zA-Z0-9-_.]+$': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'version': {'type': 'integer'},
                    'addr': {
                        'type': 'string',
                        'anyOf': [
                            {'format': 'ipv4'},
                            {'format': 'ipv6'}
                        ]
                    }
                },
                'required': ['version', 'addr']
            }
        }
    }
}

response_header = {
    'connection': {'type': 'string'},
    'content-length': {'type': 'string'},
    'content-type': {'type': 'string'},
    'status': {'type': 'string'},
    'x-compute-request-id': {'type': 'string'},
    'vary': {'type': 'string'},
    'x-openstack-nova-api-version': {'type': 'string'},
    'date': {
        'type': 'string',
        'format': 'data-time'
    }
}
