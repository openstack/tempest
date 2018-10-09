# Copyright 2015 NEC Corporation.  All rights reserved.
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

create_volume_transfer = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'transfer': {
                'type': 'object',
                'properties': {
                    'auth_key': {'type': 'string'},
                    'links': parameter_types.links,
                    'created_at': parameter_types.date_time,
                    'volume_id': {'type': 'string', 'format': 'uuid'},
                    'id': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': ['string', 'null']}
                },
                'additionalProperties': False,
                'required': ['auth_key', 'links', 'created_at',
                             'volume_id', 'id', 'name']
            }
        },
        'additionalProperties': False,
        'required': ['transfer']
    }
}

common_show_volume_transfer = {
    'type': 'object',
    'properties': {
        'links': parameter_types.links,
        'created_at': parameter_types.date_time,
        'volume_id': {'type': 'string', 'format': 'uuid'},
        'id': {'type': 'string', 'format': 'uuid'},
        'name': {'type': ['string', 'null']}
    },
    'additionalProperties': False,
    'required': ['links', 'created_at', 'volume_id', 'id', 'name']
}

show_volume_transfer = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'transfer': common_show_volume_transfer
        },
        'additionalProperties': False,
        'required': ['transfer']
    }
}

list_volume_transfers_no_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'transfers': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'volume_id': {'type': 'string', 'format': 'uuid'},
                        'id': {'type': 'string', 'format': 'uuid'},
                        'links': parameter_types.links,
                        'name': {'type': ['string', 'null']}
                    },
                    'additionalProperties': False,
                    'required': ['volume_id', 'id', 'links', 'name']
                }
            }
        },
        'additionalProperties': False,
        'required': ['transfers'],
    }
}

list_volume_transfers_with_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'transfers': {
                'type': 'array',
                'items': common_show_volume_transfer
            }
        },
        'additionalProperties': False,
        'required': ['transfers'],
    }
}

delete_volume_transfer = {'status_code': [202]}

accept_volume_transfer = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'transfer': {
                'type': 'object',
                'properties': {
                    'links': parameter_types.links,
                    'volume_id': {'type': 'string', 'format': 'uuid'},
                    'id': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': ['string', 'null']}
                },
                'additionalProperties': False,
                'required': ['links', 'volume_id', 'id', 'name']
            }
        },
        'additionalProperties': False,
        'required': ['transfer']
    }
}
