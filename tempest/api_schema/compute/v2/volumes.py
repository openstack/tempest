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

get_volume = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volume': {
                'type': 'object',
                'properties': {
                    # NOTE: Now the type of 'id' is integer, but here allows
                    # 'string' also because we will be able to change it to
                    # 'uuid' in the future.
                    'id': {'type': ['integer', 'string']},
                    'status': {'type': 'string'},
                    'displayName': {'type': ['string', 'null']},
                    'availabilityZone': {'type': 'string'},
                    'createdAt': {'type': 'string'},
                    'displayDescription': {'type': ['string', 'null']},
                    'volumeType': {'type': 'string'},
                    'snapshotId': {'type': ['string', 'null']},
                    'metadata': {'type': 'object'},
                    'size': {'type': 'integer'},
                    'attachments': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': ['integer', 'string']},
                                'device': {'type': 'string'},
                                'volumeId': {'type': ['integer', 'string']},
                                'serverId': {'type': ['integer', 'string']}
                            }
                        }
                    }
                },
                'required': ['id', 'status', 'displayName', 'availabilityZone',
                             'createdAt', 'displayDescription', 'volumeType',
                             'snapshotId', 'metadata', 'size', 'attachments']
            }
        },
        'required': ['volume']
    }
}
