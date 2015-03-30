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

common_security_group_default_rule_info = {
    'type': 'object',
    'properties': {
        'from_port': {'type': 'integer'},
        'id': {'type': 'integer'},
        'ip_protocol': {'type': 'string'},
        'ip_range': {
            'type': 'object',
            'properties': {
                'cidr': {'type': 'string'}
            },
            'required': ['cidr'],
        },
        'to_port': {'type': 'integer'},
    },
    'required': ['from_port', 'id', 'ip_protocol', 'ip_range', 'to_port'],
}

create_get_security_group_default_rule = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'security_group_default_rule':
                common_security_group_default_rule_info
        },
        'required': ['security_group_default_rule']
    }
}

delete_security_group_default_rule = {
    'status_code': [204]
}

list_security_group_default_rules = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'security_group_default_rules': {
                'type': 'array',
                'items': common_security_group_default_rule_info
            }
        },
        'required': ['security_group_default_rules']
    }
}
