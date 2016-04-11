# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.lib.api_schema.response.compute.v2_1 import keypairs

get_keypair = copy.deepcopy(keypairs.get_keypair)
get_keypair['response_body']['properties']['keypair'][
    'properties'].update({'type': {'type': 'string'}})
get_keypair['response_body']['properties']['keypair'][
    'required'].append('type')

create_keypair = copy.deepcopy(keypairs.create_keypair)
create_keypair['status_code'] = [201]
create_keypair['response_body']['properties']['keypair'][
    'properties'].update({'type': {'type': 'string'}})
create_keypair['response_body']['properties']['keypair'][
    'required'].append('type')

delete_keypair = {
    'status_code': [204],
}

list_keypairs = copy.deepcopy(keypairs.list_keypairs)
list_keypairs['response_body']['properties']['keypairs'][
    'items']['properties']['keypair'][
    'properties'].update({'type': {'type': 'string'}})
list_keypairs['response_body']['properties']['keypairs'][
    'items']['properties']['keypair']['required'].append('type')
