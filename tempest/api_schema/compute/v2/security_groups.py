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

common_security_group_rule = {
    'from_port': {'type': ['integer', 'null']},
    'to_port': {'type': ['integer', 'null']},
    'group': {
        'type': 'object',
        'properties': {
            'tenant_id': {'type': 'string'},
            'name': {'type': 'string'}
        }
    },
    'ip_protocol': {'type': ['string', 'null']},
    # 'parent_group_id' can be UUID so defining it as 'string' also.
    'parent_group_id': {'type': ['string', 'integer', 'null']},
    'ip_range': {
        'type': 'object',
        'properties': {
            'cidr': {'type': 'string'}
        }
        # When optional argument is provided in request body
        # like 'group_id' then, attribute 'cidr' does not
        # comes in response body. So it is not 'required'.
    },
    'id': {'type': ['string', 'integer']}
}

common_security_group = {
    'type': 'object',
    'properties': {
        'id': {'type': ['integer', 'string']},
        'name': {'type': 'string'},
        'tenant_id': {'type': 'string'},
        'rules': {
            'type': 'array',
            'items': {
                'type': ['object', 'null'],
                'properties': common_security_group_rule
            }
        },
        'description': {'type': 'string'},
    },
    'required': ['id', 'name', 'tenant_id', 'rules', 'description'],
}

list_security_groups = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'security_groups': {
                'type': 'array',
                'items': common_security_group
            }
        },
        'required': ['security_groups']
    }
}

get_security_group = create_security_group = update_security_group = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'security_group': common_security_group
        },
        'required': ['security_group']
    }
}

delete_security_group = {
    'status_code': [202]
}

create_security_group_rule = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'security_group_rule': {
                'type': 'object',
                'properties': common_security_group_rule,
                'required': ['from_port', 'to_port', 'group', 'ip_protocol',
                             'parent_group_id', 'id', 'ip_range']
            }
        },
        'required': ['security_group_rule']
    }
}

delete_security_group_rule = {
    'status_code': [202]
}
