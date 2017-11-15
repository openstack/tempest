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
        'additionalProperties': False,
        'required': ['href', 'rel']
    }
}

mac_address = {
    'type': 'string',
    'pattern': '(?:[a-f0-9]{2}:){5}[a-f0-9]{2}'
}

ip_address = {
    'oneOf': [
        {
            'type': 'string',
            'oneOf': [
                {'format': 'ipv4'},
                {'format': 'ipv6'}
            ]
        },
        {'type': 'null'}
    ]
}

access_ip_v4 = {
    'type': 'string',
    'oneOf': [{'format': 'ipv4'}, {'enum': ['']}]
}

access_ip_v6 = {
    'type': 'string',
    'oneOf': [{'format': 'ipv6'}, {'enum': ['']}]
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
                    'version': {'enum': [4, 6]},
                    'addr': {
                        'type': 'string',
                        'oneOf': [
                            {'format': 'ipv4'},
                            {'format': 'ipv6'}
                        ]
                    }
                },
                'additionalProperties': False,
                'required': ['version', 'addr']
            }
        }
    }
}

date_time = {
    'type': 'string',
    'format': 'iso8601-date-time'
}

date_time_or_null = {
    'type': ['string', 'null'],
    'format': 'iso8601-date-time'
}

response_header = {
    'connection': {'type': 'string'},
    'content-length': {'type': 'string'},
    'content-type': {'type': 'string'},
    'status': {'type': 'string'},
    'x-compute-request-id': {'type': 'string'},
    'vary': {'type': 'string'},
    'x-openstack-nova-api-version': {'type': 'string'},
    # NOTE(gmann): Validating this as string only as this
    # date in header is returned in different format than
    # ISO 8601 date time format which is not consistent with
    # other date-time format in nova.
    # This API is already deprecated so not worth to fix
    # on nova side.
    'date': {
        'type': 'string'
    }
}

power_state = {
    'type': 'integer',
    # 0: NOSTATE
    # 1: RUNNING
    # 3: PAUSED
    # 4: SHUTDOWN
    # 6: CRASHED
    # 7: SUSPENDED
    'enum': [0, 1, 3, 4, 6, 7]
}
