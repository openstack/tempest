# Copyright 2015 Fujitsu(fnst) Corporation
# All Rights Reserved.
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

common_snapshot_info = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'volumeId': {'type': 'string'},
        'status': {'type': 'string'},
        'size': {'type': 'integer'},
        'createdAt': parameter_types.date_time,
        'displayName': {'type': ['string', 'null']},
        'displayDescription': {'type': ['string', 'null']}
    },
    'additionalProperties': False,
    'required': ['id', 'volumeId', 'status', 'size',
                 'createdAt', 'displayName', 'displayDescription']
}

create_get_snapshot = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'snapshot': common_snapshot_info
        },
        'additionalProperties': False,
        'required': ['snapshot']
    }
}

list_snapshots = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'snapshots': {
                'type': 'array',
                'items': common_snapshot_info
            }
        },
        'additionalProperties': False,
        'required': ['snapshots']
    }
}

delete_snapshot = {
    'status_code': [202]
}
