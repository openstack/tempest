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
from tempest.api_schema.compute import hypervisors

hypervisors_servers = copy.deepcopy(hypervisors.common_hypervisors_detail)

# Defining extra attributes for V3 show hypervisor schema
hypervisors_servers['response_body']['properties']['hypervisors']['items'][
    'properties']['servers'] = {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                # NOTE: Now the type of 'id' is integer,
                # but here allows 'string' also because we
                # will be able to change it to 'uuid' in
                # the future.
                'id': {'type': ['integer', 'string']},
                'name': {'type': 'string'}
            }
        }
    }
# In V2 API, if there is no servers (VM) on the Hypervisor host then 'servers'
# attribute will not be present in response body So it is not 'required'.
