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

manage_snapshot = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'snapshot': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'size': {'type': 'integer'},
                    'metadata': {
                        'type': 'object',
                        'patternProperties': {
                            '^.+$': {'type': 'string'}
                        }
                    },
                    'name': {'type': ['string', 'null']},
                    'volume_id': {'type': 'string', 'format': 'uuid'},
                    'created_at': parameter_types.date_time,
                    'description': {'type': ['string', 'null']},
                    'id': {'type': 'string', 'format': 'uuid'},
                    'updated_at': parameter_types.date_time_or_null
                },
                'additionalProperties': False,
                'required': ['status', 'size', 'volume_id',
                             'created_at', 'description', 'id', 'updated_at']
            }
        },
        'additionalProperties': False,
        'required': ['snapshot']
    }
}
