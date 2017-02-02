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

import copy

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types


_version = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'links': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'href': {'type': 'string', 'format': 'uri'},
                    'rel': {'type': 'string'},
                    'type': {'type': 'string'},
                },
                'required': ['href', 'rel'],
                'additionalProperties': False
            }
        },
        'status': {'type': 'string'},
        'updated': parameter_types.date_time,
        'version': {'type': 'string'},
        'min_version': {'type': 'string'},
        'media-types': {
            'type': 'array',
            'properties': {
                'base': {'type': 'string'},
                'type': {'type': 'string'},
            }
        },
    },
    # NOTE: version and min_version have been added since Kilo,
    # so they should not be required.
    # NOTE(sdague): media-types only shows up in single version requests.
    'required': ['id', 'links', 'status', 'updated'],
    'additionalProperties': False
}

list_versions = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'versions': {
                'type': 'array',
                'items': _version
            }
        },
        'required': ['versions'],
        'additionalProperties': False
    }
}


_detail_get_version = copy.deepcopy(_version)
_detail_get_version['properties'].pop('min_version')
_detail_get_version['properties'].pop('version')
_detail_get_version['properties'].pop('updated')
_detail_get_version['properties']['media-types'] = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'base': {'type': 'string'},
            'type': {'type': 'string'}
        }
    }
}
_detail_get_version['required'] = ['id', 'links', 'status', 'media-types']

get_version = {
    'status_code': [300],
    'response_body': {
        'type': 'object',
        'properties': {
            'choices': {
                'type': 'array',
                'items': _detail_get_version
            }
        },
        'required': ['choices'],
        'additionalProperties': False
    }
}

get_one_version = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'version': _version
        },
        'additionalProperties': False
    }
}
