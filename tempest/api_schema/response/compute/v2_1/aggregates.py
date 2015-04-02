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

import copy

# create-aggregate api doesn't have 'hosts' and 'metadata' attributes.
aggregate_for_create = {
    'type': 'object',
    'properties': {
        'availability_zone': {'type': ['string', 'null']},
        'created_at': {'type': 'string'},
        'deleted': {'type': 'boolean'},
        'deleted_at': {'type': ['string', 'null']},
        'id': {'type': 'integer'},
        'name': {'type': 'string'},
        'updated_at': {'type': ['string', 'null']}
    },
    'required': ['availability_zone', 'created_at', 'deleted',
                 'deleted_at', 'id', 'name', 'updated_at'],
}

common_aggregate_info = copy.deepcopy(aggregate_for_create)
common_aggregate_info['properties'].update({
    'hosts': {'type': 'array'},
    'metadata': {'type': 'object'}
})
common_aggregate_info['required'].extend(['hosts', 'metadata'])

list_aggregates = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'aggregates': {
                'type': 'array',
                'items': common_aggregate_info
            }
        },
        'required': ['aggregates'],
    }
}

get_aggregate = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'aggregate': common_aggregate_info
        },
        'required': ['aggregate'],
    }
}

aggregate_set_metadata = get_aggregate
# The 'updated_at' attribute of 'update_aggregate' can't be null.
update_aggregate = copy.deepcopy(get_aggregate)
update_aggregate['response_body']['properties']['aggregate']['properties'][
    'updated_at'] = {
        'type': 'string'
    }

delete_aggregate = {
    'status_code': [200]
}

create_aggregate = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'aggregate': aggregate_for_create
        },
        'required': ['aggregate'],
    }
}

aggregate_add_remove_host = get_aggregate
