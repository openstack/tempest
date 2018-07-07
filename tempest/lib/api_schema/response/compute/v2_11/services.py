# Copyright 2017 AT&T Corporation.
# All rights reserved.
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

from tempest.lib.api_schema.response.compute.v2_1 import services


list_services = copy.deepcopy(services.list_services)
list_services['response_body']['properties']['services']['items'][
    'properties']['forced_down'] = {'type': 'boolean'}
list_services['response_body']['properties']['services']['items'][
    'required'].append('forced_down')

update_forced_down = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'service': {
                'type': 'object',
                'properties': {
                    'binary': {'type': 'string'},
                    'host': {'type': 'string'},
                    'forced_down': {'type': 'boolean'}
                },
                'additionalProperties': False,
                'required': ['binary', 'host', 'forced_down']
            }
        },
        'additionalProperties': False,
        'required': ['service']
    }
}

# **** Schemas unchanged in microversion 2.11 since microversion 2.1 ****
# Note(felipemonteiro): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
enable_disable_service = copy.deepcopy(services.enable_disable_service)
disable_log_reason = copy.deepcopy(services.disable_log_reason)
