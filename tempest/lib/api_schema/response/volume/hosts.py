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

show_host = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'host': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'resource': {
                            'type': 'object',
                            'properties': {
                                'volume_count': {'type': 'string'},
                                'total_volume_gb': {'type': 'string'},
                                'total_snapshot_gb': {'type': 'string'},
                                'project': {'type': 'string'},
                                'host': {'type': 'string'},
                                'snapshot_count': {'type': 'string'},
                            },
                            'additionalProperties': False,
                            'required': ['volume_count', 'total_volume_gb',
                                         'total_snapshot_gb', 'project',
                                         'host', 'snapshot_count'],
                        }
                    },
                    'additionalProperties': False,
                    'required': ['resource']
                }
            }
        },
        'additionalProperties': False,
        'required': ['host']
    }
}

list_hosts = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'hosts': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'service-status': {
                            'enum': ['available', 'unavailable']},
                        'service': {'type': 'string'},
                        'zone': {'type': 'string'},
                        'service-state': {
                            'enum': ['enabled', 'disabled']},
                        'host_name': {'type': 'string'},
                        'last-update': parameter_types.date_time_or_null
                    },
                    'additionalProperties': False,
                    'required': ['service-status', 'service', 'zone',
                                 'service-state', 'host_name', 'last-update']
                }
            }
        },
        'additionalProperties': False,
        'required': ['hosts']
    }
}
