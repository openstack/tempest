# Copyright 2022 NEC Corporation.  All rights reserved.
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

create = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'events': {
                'type': 'array', 'minItems': 1,
                'items': {
                    'type': 'object',
                    'properties': {
                        'server_uuid': {
                            'type': 'string', 'format': 'uuid'
                        },
                        'name': {
                            'type': 'string',
                            'enum': [
                                'network-changed',
                                'network-vif-plugged',
                                'network-vif-unplugged',
                                'network-vif-deleted'
                            ],
                        },
                        'status': {
                            'type': 'string',
                            'enum': ['failed', 'completed', 'in-progress'],
                        },
                        'tag': {
                            'type': 'string', 'maxLength': 255,
                        },
                        'code': {'type': 'integer'},
                    },
                    'required': [
                        'server_uuid', 'name', 'code'],
                    'additionalProperties': False,
                },
            },
        },
        'required': ['events'],
        'additionalProperties': False,
    }
}
