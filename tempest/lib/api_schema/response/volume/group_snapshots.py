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

create_group_snapshot = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_snapshot': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                    'group_type_id': {'type': 'string', 'format': 'uuid'},
                },
                'additionalProperties': False,
                'required': ['id', 'name', 'group_type_id']
            }
        },
        'additionalProperties': False,
        'required': ['group_snapshot']
    }
}

delete_group_snapshot = {'status_code': [202]}

common_show_group_snapshot = {
    'type': 'object',
    'properties': {
        'created_at': parameter_types.date_time,
        'group_id': {'type': 'string', 'format': 'uuid'},
        'id': {'type': 'string', 'format': 'uuid'},
        'name': {'type': 'string'},
        'status': {'type': 'string'},
        'description': {'type': ['string', 'null']},
        'group_type_id': {'type': 'string', 'format': 'uuid'},
    },
    'additionalProperties': False,
    'required': ['created_at', 'group_id', 'id', 'name',
                 'status', 'description', 'group_type_id']
}

show_group_snapshot = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_snapshot': common_show_group_snapshot
        },
        'additionalProperties': False,
        'required': ['group_snapshot']
    }
}

list_group_snapshots_no_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_snapshots': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string', 'format': 'uuid'},
                        'name': {'type': 'string'}
                    },
                    'additionalProperties': False,
                    'required': ['id', 'name'],
                }
            }
        },
        'additionalProperties': False,
        'required': ['group_snapshots'],
    }
}

list_group_snapshots_with_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_snapshots': {
                'type': 'array',
                'items': common_show_group_snapshot
            }
        },
        'additionalProperties': False,
        'required': ['group_snapshots'],
    }
}

reset_group_snapshot_status = {'status_code': [202]}
