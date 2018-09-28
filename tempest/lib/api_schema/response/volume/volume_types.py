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

extra_specs_info = {
    'type': 'object',
    'patternProperties': {
        '^.+$': {'type': 'string'}
    }
}

common_show_volume_type = {
    'type': 'object',
    'properties': {
        'extra_specs': extra_specs_info,
        'name': {'type': 'string'},
        'is_public': {'type': 'boolean'},
        'description': {'type': ['string', 'null']},
        'id': {'type': 'string', 'format': 'uuid'},
        'os-volume-type-access:is_public': {'type': 'boolean'},
        'qos_specs_id': {'type': ['string', 'null'], 'format': 'uuid'}
    },
    'additionalProperties': False,
    'required': ['name', 'is_public', 'description', 'id',
                 'os-volume-type-access:is_public']
}

show_volume_type = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volume_type': common_show_volume_type,
        },
        'additionalProperties': False,
        'required': ['volume_type']
    }
}

delete_volume_type = {'status_code': [202]}

create_volume_type = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volume_type': {
                'type': 'object',
                'properties': {
                    'extra_specs': extra_specs_info,
                    'name': {'type': 'string'},
                    'is_public': {'type': 'boolean'},
                    'description': {'type': ['string', 'null']},
                    'id': {'type': 'string', 'format': 'uuid'},
                    'os-volume-type-access:is_public': {'type': 'boolean'}
                },
                'additionalProperties': False,
                'required': ['name', 'is_public', 'id',
                             'description', 'os-volume-type-access:is_public']
            },
        },
        'additionalProperties': False,
        'required': ['volume_type']
    }
}

list_volume_types = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volume_types': {
                'type': 'array',
                'items': common_show_volume_type
            }
        },
        'additionalProperties': False,
        'required': ['volume_types']
    }
}

list_volume_types_extra_specs = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'extra_specs': extra_specs_info
        },
        'additionalProperties': False,
        'required': ['extra_specs']
    }
}

show_volume_types_extra_specs = {
    'status_code': [200],
    'response_body': extra_specs_info
}

create_volume_types_extra_specs = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'extra_specs': extra_specs_info
        },
        'additionalProperties': False,
        'required': ['extra_specs']
    }
}

delete_volume_types_extra_specs = {'status_code': [202]}

update_volume_types = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volume_type': {
                'type': 'object',
                'properties': {
                    'extra_specs': extra_specs_info,
                    'name': {'type': 'string'},
                    'is_public': {'type': 'boolean'},
                    'description': {'type': ['string', 'null']},
                    'id': {'type': 'string', 'format': 'uuid'}
                },
                'additionalProperties': False,
                'required': ['name', 'is_public', 'description', 'id']
            },
        },
        'additionalProperties': False,
        'required': ['volume_type']
    }
}

update_volume_type_extra_specs = {
    'status_code': [200],
    'response_body': extra_specs_info
}

add_type_access = {'status_code': [202]}

remove_type_access = {'status_code': [202]}

list_type_access = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volume_type_access': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'volume_type_id': {'type': 'string', 'format': 'uuid'},
                        'project_id': {'type': 'string', 'format': 'uuid'},
                    },
                    'additionalProperties': False,
                    'required': ['volume_type_id', 'project_id']
                }
            }
        },
        'additionalProperties': False,
        'required': ['volume_type_access']
    }
}
