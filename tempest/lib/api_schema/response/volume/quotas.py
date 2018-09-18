# Copyright 2019 ZTE Corporation.  All rights reserved.
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

delete_quota_set = {
    'status_code': [200],
}

quota_usage_info = {
    'type': 'object',
    'properties': {
        'reserved': {'type': 'integer'},
        'allocated': {'type': 'integer'},
        'limit': {'type': 'integer'},
        'in_use': {'type': 'integer'}
    },
    'additionalProperties': False,
    # 'allocated' attribute is available only when nested quota is enabled.
    'required': ['reserved', 'limit', 'in_use'],
}

show_quota_set = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'quota_set': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'volumes': {'type': 'integer'},
                    'snapshots': {'type': 'integer'},
                    'backups': {'type': 'integer'},
                    'groups': {'type': 'integer'},
                    'per_volume_gigabytes': {'type': 'integer'},
                    'gigabytes': {'type': 'integer'},
                    'backup_gigabytes': {'type': 'integer'},
                },
                # for volumes_{volume_type}, etc
                "additionalProperties": {'type': 'integer'},
                'required': ['id', 'volumes', 'snapshots', 'backups',
                             'per_volume_gigabytes', 'gigabytes',
                             'backup_gigabytes', 'groups'],
            }
        },
        'required': ['quota_set']
    }
}

update_quota_set = copy.deepcopy(show_quota_set)
update_quota_set['response_body']['properties']['quota_set'][
    'required'].remove('id')

show_quota_set_usage = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'quota_set': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'volumes': quota_usage_info,
                    'snapshots': quota_usage_info,
                    'backups': quota_usage_info,
                    'groups': quota_usage_info,
                    'per_volume_gigabytes': quota_usage_info,
                    'gigabytes': quota_usage_info,
                    'backup_gigabytes': quota_usage_info,
                },
                # for volumes_{volume_type}, etc
                "additionalProperties": quota_usage_info,
                'required': ['id', 'volumes', 'snapshots', 'backups',
                             'per_volume_gigabytes', 'gigabytes',
                             'backup_gigabytes', 'groups'],
            }
        },
        'required': ['quota_set']
    }
}
