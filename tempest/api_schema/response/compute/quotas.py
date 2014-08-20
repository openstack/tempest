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

common_quota_set = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'quota_set': {
                'type': 'object',
                'properties': {
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
                'required': ['instances', 'cores', 'ram',
                             'floating_ips', 'fixed_ips',
                             'metadata_items', 'key_pairs',
                             'security_groups', 'security_group_rules']
            }
        },
        'required': ['quota_set']
    }
}
