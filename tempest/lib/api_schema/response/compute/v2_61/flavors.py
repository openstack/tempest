# Copyright 2018 NEC Corporation.  All rights reserved.
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
from tempest.lib.api_schema.response.compute.v2_55 import flavors \
    as flavorsv255

# ****** Schemas changed in microversion 2.61 *****************

# Note(gmann): This is schema for microversion 2.61 which includes the
# Flavor extra_specs in the Response body of the following APIs:
#    - ``PUT /flavors/{flavor_id}``
#    - ``GET /flavors/detail``
#    - ``GET /flavors/{flavor_id}``
#    - ``POST /flavors``

flavor_description = {
    'type': ['string', 'null'],
    'minLength': 0, 'maxLength': 65535
}

flavor_extra_specs = {
    'type': 'object',
    'patternProperties': {
        '^[a-zA-Z0-9-_:. ]{1,255}$': {'type': 'string'}
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
        'OS-FLV-EXT-DATA:ephemeral': {'type': 'integer'},
        'description': flavor_description,
        'extra_specs': flavor_extra_specs
    },
    'additionalProperties': False,
    # 'OS-FLV-DISABLED', 'os-flavor-access', 'rxtx_factor' and
    # 'OS-FLV-EXT-DATA' are API extensions. so they are not 'required'.
    'required': ['name', 'links', 'ram', 'vcpus', 'swap', 'disk', 'id',
                 'description']
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
            # to be present always so it is not 'required'.
            'flavors_links': parameter_types.links
        },
        'additionalProperties': False,
        'required': ['flavors']
    }
}

create_update_get_flavor_details = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'flavor': common_flavor_info
        },
        'additionalProperties': False,
        'required': ['flavor']
    }
}

# ****** Schemas unchanged in microversion 2.61 since microversion 2.55 ***
# Note(gmann): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.55 ***
list_flavors = copy.deepcopy(flavorsv255.list_flavors)

# ****** Schemas unchanged since microversion 2.1 ***
delete_flavor = copy.deepcopy(flavorsv255.delete_flavor)
