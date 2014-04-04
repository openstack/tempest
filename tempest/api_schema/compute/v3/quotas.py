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

quota_set = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'quota_set': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'instances': {'type': 'integer'},
                    'cores': {'type': 'integer'},
                    'ram': {'type': 'integer'},
                    'floating_ips': {'type': 'integer'},
                    'fixed_ips': {'type': 'integer'},
                    'metadata_items': {'type': 'integer'},
                    'key_pairs': {'type': 'integer'},
                    'security_groups': {'type': 'integer'},
                    'security_group_rules': {'type': 'integer'}
                },
                'required': ['id', 'instances', 'cores', 'ram',
                             'floating_ips', 'fixed_ips',
                             'metadata_items', 'key_pairs',
                             'security_groups', 'security_group_rules']
            }
        },
        'required': ['quota_set']
    }
}

quota_common_info = {
    'type': 'object',
    'properties': {
        'reserved': {'type': 'integer'},
        'limit': {'type': 'integer'},
        'in_use': {'type': 'integer'}
    },
    'required': ['reserved', 'limit', 'in_use']
}

quota_set_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'quota_set': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'instances': quota_common_info,
                    'cores': quota_common_info,
                    'ram': quota_common_info,
                    'floating_ips': quota_common_info,
                    'fixed_ips': quota_common_info,
                    'metadata_items': quota_common_info,
                    'key_pairs': quota_common_info,
                    'security_groups': quota_common_info,
                    'security_group_rules': quota_common_info
                },
                'required': ['id', 'instances', 'cores', 'ram',
                             'floating_ips', 'fixed_ips',
                             'metadata_items', 'key_pairs',
                             'security_groups', 'security_group_rules']
            }
        },
        'required': ['quota_set']
    }
}
