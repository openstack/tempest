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

create_keypair = {
    'type': 'object',
    'properties': {
        'keypair': {
            'type': 'object',
            'properties': {
                'fingerprint': {'type': 'string'},
                'name': {'type': 'string'},
                'public_key': {'type': 'string'},
                # NOTE: Now the type of 'user_id' is integer, but here
                # allows 'string' also because we will be able to change
                # it to 'uuid' in the future.
                'user_id': {'type': ['integer', 'string']},
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
