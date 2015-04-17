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

get_keypair = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'keypair': {
                'type': 'object',
                'properties': {
                    'public_key': {'type': 'string'},
                    'name': {'type': 'string'},
                    'fingerprint': {'type': 'string'},
                    'user_id': {'type': 'string'},
                    'deleted': {'type': 'boolean'},
                    'created_at': {'type': 'string'},
                    'updated_at': {'type': ['string', 'null']},
                    'deleted_at': {'type': ['string', 'null']},
                    'id': {'type': 'integer'}

                },
                # When we run the get keypair API, response body includes
                # all the above mentioned attributes.
                # But in Nova API sample file, response body includes only
                # 'public_key', 'name' & 'fingerprint'. So only 'public_key',
                # 'name' & 'fingerprint' are defined as 'required'.
                'required': ['public_key', 'name', 'fingerprint']
            }
        },
        'required': ['keypair']
    }
}

create_keypair = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'keypair': {
                'type': 'object',
                'properties': {
                    'fingerprint': {'type': 'string'},
                    'name': {'type': 'string'},
                    'public_key': {'type': 'string'},
                    'user_id': {'type': 'string'},
                    'private_key': {'type': 'string'}
                },
                # When create keypair API is being called with 'Public key'
                # (Importing keypair) then, response body does not contain
                # 'private_key' So it is not defined as 'required'
                'required': ['fingerprint', 'name', 'public_key', 'user_id']
            }
        },
        'required': ['keypair']
    }
}

delete_keypair = {
    'status_code': [202],
}

list_keypairs = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'keypairs': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'keypair': {
                            'type': 'object',
                            'properties': {
                                'public_key': {'type': 'string'},
                                'name': {'type': 'string'},
                                'fingerprint': {'type': 'string'}
                            },
                            'required': ['public_key', 'name', 'fingerprint']
                        }
                    },
                    'required': ['keypair']
                }
            }
        },
        'required': ['keypairs']
    }
}
