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

from tempest.api_schema.response.compute import availability_zone as common


base = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'availabilityZoneInfo': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'zoneName': {'type': 'string'},
                        'zoneState': {
                            'type': 'object',
                            'properties': {
                                'available': {'type': 'boolean'}
                            },
                            'required': ['available']
                        },
                        # NOTE: Here is the difference between detail and
                        # non-detail.
                        'hosts': {'type': 'null'}
                    },
                    'required': ['zoneName', 'zoneState', 'hosts']
                }
            }
        },
        'required': ['availabilityZoneInfo']
    }
}

get_availability_zone_list = copy.deepcopy(base)

get_availability_zone_list_detail = copy.deepcopy(base)
get_availability_zone_list_detail['response_body']['properties'][
    'availabilityZoneInfo']['items']['properties']['hosts'] = common.detail
