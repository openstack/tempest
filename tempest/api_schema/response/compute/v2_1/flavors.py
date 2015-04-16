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

from tempest.api_schema.response.compute import parameter_types

list_flavors = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'flavors': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'links': parameter_types.links,
                        'id': {'type': 'string'}
                    },
                    'required': ['name', 'links', 'id']
                }
            },
            'flavors_links': parameter_types.links
        },
        # NOTE(gmann): flavors_links attribute is not necessary
        # to be present always So it is not 'required'.
        'required': ['flavors']
    }
}

common_flavor_info = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'links': parameter_types.links,
        'ram': {'type': 'integer'},
        'vcpus': {'type': 'integer'},
        # 'swap' attributes comes as integer value but if it is empty
        # it comes as "". So defining type of as string and integer.
        'swap': {'type': ['integer', 'string']},
        'disk': {'type': 'integer'},
        'id': {'type': 'string'},
        'OS-FLV-DISABLED:disabled': {'type': 'boolean'},
        'os-flavor-access:is_public': {'type': 'boolean'},
        'rxtx_factor': {'type': 'number'},
        'OS-FLV-EXT-DATA:ephemeral': {'type': 'integer'}
    },
    # 'OS-FLV-DISABLED', 'os-flavor-access', 'rxtx_factor' and
    # 'OS-FLV-EXT-DATA' are API extensions. So they are not 'required'.
    'required': ['name', 'links', 'ram', 'vcpus', 'swap', 'disk', 'id']
}

list_flavors_details = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'flavors': {
                'type': 'array',
                'items': common_flavor_info
            },
            # NOTE(gmann): flavors_links attribute is not necessary
            # to be present always So it is not 'required'.
            'flavors_links': parameter_types.links
        },
        'required': ['flavors']
    }
}

unset_flavor_extra_specs = {
    'status_code': [200]
}

create_get_flavor_details = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'flavor': common_flavor_info
        },
        'required': ['flavor']
    }
}

delete_flavor = {
    'status_code': [202]
}
