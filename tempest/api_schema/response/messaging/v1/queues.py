
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

age = {
    'type': 'number',
    'minimum': 0
}

message_link = {
    'type': 'object',
    'properties': {
        'href': {
            'type': 'string',
            'format': 'uri'
        },
        'age': age,
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

resource_schema = {
    'type': 'array',
    'items': {
        'type': 'string'
    },
    'minItems': 1
}

post_messages = {
    'status_code': [201],
    'response_body': {
        'type': 'object',
        'properties': {
            'resources': resource_schema,
            'partial': {'type': 'boolean'}
        }
    },
    'required': ['resources', 'partial']
}

message_ttl = {
    'type': 'number',
    'minimum': 1
}

list_messages_links = {
    'type': 'array',
    'maxItems': 1,
    'minItems': 1,
    'items': {
        'type': 'object',
        'properties': {
            'rel': {'type': 'string'},
            'href': {'type': 'string'}
        },
        'required': ['rel', 'href']
    }
}

list_messages_response = {
    'type': 'array',
    'minItems': 1,
    'items': {
        'type': 'object',
        'properties': {
            'href': {'type': 'string'},
            'ttl': message_ttl,
            'age': age,
            'body': {'type': 'object'}
        },
        'required': ['href', 'ttl', 'age', 'body']
    }
}

list_messages = {
    'status_code': [200, 204],
    'response_body': {
        'type': 'object',
        'properties': {
            'links': list_messages_links,
            'messages': list_messages_response
        }
    },
    'required': ['links', 'messages']
}

single_message = {
    'type': 'object',
    'properties': {
        'href': {'type': 'string'},
        'ttl': message_ttl,
        'age': age,
        'body': {'type': 'object'}
    },
    'required': ['href', 'ttl', 'age', 'body']
}

get_single_message = {
    'status_code': [200],
    'response_body': single_message
}

get_multiple_messages = {
    'status_code': [200],
    'response_body': {
        'type': 'array',
        'items': single_message,
        'minItems': 1
    }
}

messages_claimed = {
    'type': 'object',
    'properties': {
        'href': {
            'type': 'string',
            'format': 'uri'
        },
        'ttl': message_ttl,
        'age': {'type': 'number'},
        'body': {'type': 'object'}
    },
    'required': ['href', 'ttl', 'age', 'body']
}

claim_messages = {
    'status_code': [201, 204],
    'response_body': {
        'type': 'array',
        'items': messages_claimed,
        'minItems': 1
    }
}

claim_ttl = {
    'type': 'number',
    'minimum': 1
}

query_claim = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'age': {'type': 'number'},
            'ttl': claim_ttl,
            'messages': {
                'type': 'array',
                'minItems': 1
            }
        },
        'required': ['ttl', 'age', 'messages']
    }
}
