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

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

show_encryption_type = {
    'status_code': [200],
    'response_body': {
        'type': ['object', 'null'],
        'properties': {
            'volume_type_id': {'type': 'string', 'format': 'uuid'},
            'encryption_id': {'type': 'string', 'format': 'uuid'},
            'key_size': {'type': ['integer', 'null']},
            'provider': {'type': 'string'},
            'control_location': {'enum': ['front-end', 'back-end']},
            'cipher': {'type': ['string', 'null']},
            'deleted': {'type': 'boolean'},
            'created_at': parameter_types.date_time,
            'updated_at': parameter_types.date_time_or_null,
            'deleted_at': parameter_types.date_time_or_null
        },
        # result of show_encryption_type may be empty list,
        # so no required fields.
        'additionalProperties': False,
    }
}

show_encryption_specs_item = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'patternProperties': {
            '^.+$': {'type': 'string'}
        }
    }
}

create_encryption_type = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'encryption': {
                'type': 'object',
                'properties': {
                    'volume_type_id': {'type': 'string', 'format': 'uuid'},
                    'encryption_id': {'type': 'string', 'format': 'uuid'},
                    'key_size': {'type': ['integer', 'null']},
                    'provider': {'type': 'string'},
                    'control_location': {'enum': ['front-end', 'back-end']},
                    'cipher': {'type': ['string', 'null']},
                },
                'additionalProperties': False,
                'required': ['volume_type_id', 'encryption_id']
            }
        },
        'additionalProperties': False,
        'required': ['encryption']
    }
}

delete_encryption_type = {'status_code': [202]}

update_encryption_type = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'encryption': {
                'type': 'object',
                'properties': {
                    'key_size': {'type': ['integer', 'null']},
                    'provider': {'type': 'string'},
                    'control_location': {'enum': ['front-end', 'back-end']},
                    'cipher': {'type': ['string', 'null']},
                },
                # all fields are optional
                'additionalProperties': False,
            }
        },
        'additionalProperties': False,
        'required': ['encryption']
    }
}
