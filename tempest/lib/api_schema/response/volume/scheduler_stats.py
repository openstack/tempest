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
from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

get_pools_no_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'pools': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                    },
                    'additionalProperties': False,
                    'required': ['name']
                }
            }
        },
        'additionalProperties': False,
        'required': ['pools'],
    }
}

get_pools_with_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'pools': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'capabilities': {
                            'type': ['object', 'null'],
                            'properties': {
                                'updated': parameter_types.date_time_or_null,
                                'QoS_support': {'type': 'boolean'},
                                'total_capacity_gb': {
                                    'type': ['number', 'string']
                                },
                                'volume_backend_name': {'type': 'string'},
                                'free_capacity_gb': {
                                    'type': ['number', 'string']
                                },
                                'driver_version': {'type': 'string'},
                                'reserved_percentage': {'type': 'integer'},
                                'storage_protocol': {'type': 'string'},
                                'vendor_name': {'type': 'string'},
                                'timestamp': parameter_types.date_time_or_null
                            },
                            # Because some legacy volumes or backends may not
                            # support pools, so no required fields here.
                        },
                    },
                    'additionalProperties': False,
                    'required': ['name', 'capabilities']
                }
            }
        },
        'additionalProperties': False,
        'required': ['pools'],
    }
}
