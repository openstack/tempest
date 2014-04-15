
# Copyright (c) 2014 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

list_link = {
    'type': 'object',
    'properties': {
        'rel': {'type': 'string'},
        'href': {
            'type': 'string',
            'format': 'uri'
        }
    },
    'required': ['href', 'rel']
}

list_queue = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'href': {
            'type': 'string',
            'format': 'uri'
        },
        'metadata': {'type': 'object'}
    },
    'required': ['name', 'href']
}

list_queues = {
    'status_code': [200, 204],
    'response_body': {
        'type': 'object',
        'properties': {
            'links': {
                'type': 'array',
                'items': list_link,
                'maxItems': 1
            },
            'queues': {
                'type': 'array',
                'items': list_queue
            }
        },
        'required': ['links', 'queues']
    }
}

message_link = {
    'type': 'object',
    'properties': {
        'href': {
            'type': 'string',
            'format': 'uri'
        },
        'age': {'type': 'number'},
        'created': {
            'type': 'string',
            'format': 'date-time'
        }
    },
    'required': ['href', 'age', 'created']
}

messages = {
    'type': 'object',
    'properties': {
        'free': {'type': 'number'},
        'claimed': {'type': 'number'},
        'total': {'type': 'number'},
        'oldest': message_link,
        'newest': message_link
    },
    'required': ['free', 'claimed', 'total']
}

queue_stats = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'messages': messages
        },
        'required': ['messages']
    }
}
