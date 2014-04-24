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

from tempest.api_schema.compute import flavors
from tempest.api_schema.compute import flavors_extra_specs

list_flavors_details = copy.deepcopy(flavors.common_flavor_list_details)

# NOTE- In v3 API, 'swap' comes as '0' not empty string '""'
# (In V2 API, it comes as empty string) So leaving 'swap'as integer type only.

# Defining extra attributes for V3 flavor schema
list_flavors_details['response_body']['properties']['flavors']['items'][
    'properties'].update({'disabled': {'type': 'boolean'},
                          'ephemeral': {'type': 'integer'},
                          'flavor-access:is_public': {'type': 'boolean'},
                          'os-flavor-rxtx:rxtx_factor': {'type': 'number'}})
# 'flavor-access' and 'os-flavor-rxtx' are API extensions.
# So they are not 'required'.
list_flavors_details['response_body']['properties']['flavors']['items'][
    'required'].extend(['disabled', 'ephemeral'])

set_flavor_extra_specs = copy.deepcopy(flavors_extra_specs.flavor_extra_specs)
set_flavor_extra_specs['status_code'] = [201]

unset_flavor_extra_specs = {
    'status_code': [204]
}
