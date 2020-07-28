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

group_specs = {
    'type': 'object',
    'patternProperties': {
        '^.+$': {'type': 'string'}
    }
}

common_show_group_type = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'is_public': {'type': 'boolean'},
        'group_specs': group_specs,
        'description': {'type': ['string', 'null']},
        'name': {'type': 'string'},
    },
    'additionalProperties': False,
    'required': ['id', 'is_public', 'description', 'name']
}

create_group_type = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_type': common_show_group_type
        },
        'additionalProperties': False,
        'required': ['group_type']
    }
}

delete_group_type = {'status_code': [202]}

list_group_types = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_types': {
                'type': 'array',
                'items': common_show_group_type
            }
        },
        'additionalProperties': False,
        'required': ['group_types'],
    }
}

show_group_type = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_type': common_show_group_type
        },
        'additionalProperties': False,
        'required': ['group_type']
    }
}

show_default_group_type = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_type': common_show_group_type
        },
        'additionalProperties': False,
        'required': ['group_type']
    }
}

update_group_type = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_type': common_show_group_type
        },
        'additionalProperties': False,
        'required': ['group_type']
    }
}

create_or_update_group_type_specs = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_specs': group_specs,
        },
        'additionalProperties': False,
        'required': ['group_specs']
    }
}

list_group_type_specs = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'group_specs': group_specs,
        },
        'additionalProperties': False,
        'required': ['group_specs']
    }
}

show_group_type_specs_item = {
    'status_code': [200],
    'response_body': group_specs
}

update_group_type_specs_item = {
    'status_code': [200],
    'response_body': group_specs
}

delete_group_type_specs_item = {'status_code': [202]}
