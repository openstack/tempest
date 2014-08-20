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

aggregate = {
    'type': 'object',
    'properties': {
        'availability_zone': {'type': ['string', 'null']},
        'created_at': {'type': 'string'},
        'deleted': {'type': 'boolean'},
        'deleted_at': {'type': ['string', 'null']},
        'hosts': {'type': 'array'},
        'id': {'type': 'integer'},
        'metadata': {'type': 'object'},
        'name': {'type': 'string'},
        'updated_at': {'type': ['string', 'null']}
    },
    'required': ['availability_zone', 'created_at', 'deleted',
                 'deleted_at', 'hosts', 'id', 'metadata',
                 'name', 'updated_at']
}

list_aggregates = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'aggregates': {
                'type': 'array',
                'items': aggregate
            }
        },
        'required': ['aggregates']
    }
}

get_aggregate = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'aggregate': aggregate
        },
        'required': ['aggregate']
    }
}

aggregate_set_metadata = get_aggregate
# The 'updated_at' attribute of 'update_aggregate' can't be null.
update_aggregate = copy.deepcopy(get_aggregate)
update_aggregate['response_body']['properties']['aggregate']['properties'][
    'updated_at'] = {
        'type': 'string'
    }

common_create_aggregate = {
    'response_body': {
        'type': 'object',
        'properties': {
            'aggregate': aggregate
        },
        'required': ['aggregate']
    }
}
# create-aggregate api doesn't have 'hosts' and 'metadata' attributes.
del common_create_aggregate['response_body']['properties']['aggregate'][
    'properties']['hosts']
del common_create_aggregate['response_body']['properties']['aggregate'][
    'properties']['metadata']
common_create_aggregate['response_body']['properties']['aggregate'][
    'required'] = ['availability_zone', 'created_at', 'deleted', 'deleted_at',
                   'id', 'name', 'updated_at']

aggregate_add_remove_host = get_aggregate
