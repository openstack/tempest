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

from tempest.api_schema.response.compute import hypervisors


list_hypervisors_detail = copy.deepcopy(
    hypervisors.common_list_hypervisors_detail)
# Defining extra attributes for V3 show hypervisor schema
list_hypervisors_detail['response_body']['properties']['hypervisors'][
    'items']['properties']['os-pci:pci_stats'] = {'type': 'array'}

show_hypervisor = copy.deepcopy(hypervisors.common_show_hypervisor)
# Defining extra attributes for V3 show hypervisor schema
show_hypervisor['response_body']['properties']['hypervisor']['properties'][
    'os-pci:pci_stats'] = {'type': 'array'}

hypervisors_servers = copy.deepcopy(hypervisors.common_hypervisors_info)

# Defining extra attributes for V3 show hypervisor schema
hypervisors_servers['response_body']['properties']['hypervisor']['properties'][
    'servers'] = {
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
# V3 API response body always contains the 'servers' attribute even there
# is no server (VM) are present on Hypervisor host.
hypervisors_servers['response_body']['properties']['hypervisor'][
    'required'] = ['id', 'hypervisor_hostname', 'servers']
