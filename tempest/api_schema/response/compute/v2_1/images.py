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

from tempest.api_schema.response.compute import parameter_types

image_links = copy.deepcopy(parameter_types.links)
image_links['items']['properties'].update({'type': {'type': 'string'}})

common_image_schema = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'status': {'type': 'string'},
        'updated': {'type': 'string'},
        'links': image_links,
        'name': {'type': 'string'},
        'created': {'type': 'string'},
        'minDisk': {'type': 'integer'},
        'minRam': {'type': 'integer'},
        'progress': {'type': 'integer'},
        'metadata': {'type': 'object'},
        'server': {
            'type': 'object',
            'properties': {
                'id': {'type': 'string'},
                'links': parameter_types.links
            },
            'required': ['id', 'links']
        },
        'OS-EXT-IMG-SIZE:size': {'type': 'integer'},
        'OS-DCF:diskConfig': {'type': 'string'}
    },
    # 'server' attributes only comes in response body if image is
    # associated with any server. 'OS-EXT-IMG-SIZE:size' & 'OS-DCF:diskConfig'
    # are API extension,  So those are not defined as 'required'.
    'required': ['id', 'status', 'updated', 'links', 'name',
                 'created', 'minDisk', 'minRam', 'progress',
                 'metadata']
}

get_image = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'image': common_image_schema
        },
        'required': ['image']
    }
}

list_images = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'images': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string'},
                        'links': image_links,
                        'name': {'type': 'string'}
                    },
                    'required': ['id', 'links', 'name']
                }
            },
            'images_links': parameter_types.links
        },
        # NOTE(gmann): images_links attribute is not necessary to be
        # present always So it is not 'required'.
        'required': ['images']
    }
}

create_image = {
    'status_code': [202],
    'response_header': {
        'type': 'object',
        'properties': parameter_types.response_header
    }
}
create_image['response_header']['properties'].update(
    {'location': {
        'type': 'string',
        'format': 'uri'}
     }
)
create_image['response_header']['required'] = ['location']

delete = {
    'status_code': [204]
}

image_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'metadata': {'type': 'object'}
        },
        'required': ['metadata']
    }
}

image_meta_item = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'meta': {'type': 'object'}
        },
        'required': ['meta']
    }
}

list_images_details = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'images': {
                'type': 'array',
                'items': common_image_schema
            },
            'images_links': parameter_types.links
        },
        # NOTE(gmann): images_links attribute is not necessary to be
        # present always So it is not 'required'.
        'required': ['images']
    }
}
