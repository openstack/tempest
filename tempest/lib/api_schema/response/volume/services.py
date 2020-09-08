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
import copy

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

list_services = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'services': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'binary': {'type': 'string'},
                        'disabled_reason': {'type': ['string', 'null']},
                        'host': {'type': 'string'},
                        'state': {'enum': ['up', 'down']},
                        'status': {'enum': ['enabled', 'disabled']},
                        'frozen': {'type': 'boolean'},
                        'updated_at': parameter_types.date_time,
                        'zone': {'type': 'string'},
                        'replication_status': {'type': 'string'},
                        'active_backend_id': {'type': ['string', 'null']},
                        'backend_state': {'type': 'string'},
                    },
                    'additionalProperties': False,
                    'required': ['binary', 'disabled_reason', 'host', 'state',
                                 'status', 'updated_at', 'zone']
                }
            }
        },
        'additionalProperties': False,
        'required': ['services']
    }
}

enable_service = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'disabled': {'type': 'boolean'},
            'status': {'enum': ['enabled', 'disabled']},
            'host': {'type': 'string'},
            'service': {'type': 'string'},
            'binary': {'type': 'string'},
            'disabled_reason': {'type': ['string', 'null']}
        },
        'additionalProperties': False,
        'required': ['disabled', 'status', 'host', 'service',
                     'binary', 'disabled_reason']
    }
}

disable_service = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'disabled': {'type': 'boolean'},
            'status': {'enum': ['enabled', 'disabled']},
            'host': {'type': 'string'},
            'service': {'type': 'string'},
            'binary': {'type': 'string'},
        },
        'additionalProperties': False,
        'required': ['disabled', 'status', 'host', 'service', 'binary']
    }
}

disable_log_reason = copy.deepcopy(enable_service)

freeze_host = {'status_code': [200]}
thaw_host = {'status_code': [200]}
