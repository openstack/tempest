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

from tempest.api_schema.response.compute import flavors

list_flavors_details = copy.deepcopy(flavors.common_flavor_list_details)

# 'swap' attributes comes as integre value but if it is empty it comes as "".
# So defining type of as string and integer.
list_flavors_details['response_body']['properties']['flavors']['items'][
    'properties']['swap'] = {'type': ['string', 'integer']}

# Defining extra attributes for V2 flavor schema
list_flavors_details['response_body']['properties']['flavors']['items'][
    'properties'].update({'OS-FLV-DISABLED:disabled': {'type': 'boolean'},
                          'os-flavor-access:is_public': {'type': 'boolean'},
                          'rxtx_factor': {'type': 'number'},
                          'OS-FLV-EXT-DATA:ephemeral': {'type': 'integer'}})
# 'OS-FLV-DISABLED', 'os-flavor-access', 'rxtx_factor' and 'OS-FLV-EXT-DATA'
# are API extensions. So they are not 'required'.

unset_flavor_extra_specs = {
    'status_code': [200]
}

create_get_flavor_details = copy.deepcopy(flavors.common_flavor_details)

# 'swap' attributes comes as integre value but if it is empty it comes as "".
# So defining type of as string and integer.
create_get_flavor_details['response_body']['properties']['flavor'][
    'properties']['swap'] = {'type': ['string', 'integer']}

# Defining extra attributes for V2 flavor schema
create_get_flavor_details['response_body']['properties']['flavor'][
    'properties'].update({'OS-FLV-DISABLED:disabled': {'type': 'boolean'},
                          'os-flavor-access:is_public': {'type': 'boolean'},
                          'rxtx_factor': {'type': 'number'},
                          'OS-FLV-EXT-DATA:ephemeral': {'type': 'integer'}})
# 'OS-FLV-DISABLED', 'os-flavor-access', 'rxtx_factor' and 'OS-FLV-EXT-DATA'
# are API extensions. So they are not 'required'.

delete_flavor = {
    'status_code': [202]
}
