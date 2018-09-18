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

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

delete_message = {
    'status_code': [204],
}

common_show_message = {
    'type': 'object',
    'properties': {
        'request_id': {'type': 'string'},
        'message_level': {'type': 'string'},
        'links': parameter_types.links,
        'event_id': {'type': 'string'},
        'created_at': parameter_types.date_time,
        'guaranteed_until': parameter_types.date_time,
        'resource_uuid': {'type': 'string', 'format': 'uuid'},
        'id': {'type': 'string', 'format': 'uuid'},
        'resource_type': {'type': 'string'},
        'user_message': {'type': 'string'}},
    'additionalProperties': False,
    'required': ['request_id', 'message_level', 'event_id', 'created_at',
                 'id', 'user_message'],
}

show_message = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'message': common_show_message
        },
        'additionalProperties': False,
        'required': ['message']
    }
}

list_messages = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'messages': {
                'type': 'array',
                'items': common_show_message
            },
        },
        'additionalProperties': False,
        'required': ['messages']
    }
}
