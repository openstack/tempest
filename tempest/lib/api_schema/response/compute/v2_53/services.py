# Copyright 2018 AT&T Corporation.
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

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types
from tempest.lib.api_schema.response.compute.v2_11 import services \
    as servicesv211

# ***************** Schemas changed in microversion 2.53 *****************

# NOTE(felipemonteiro): This is schema for microversion 2.53 which includes:
#
# * changing the service 'id' to 'string' type only
# * adding update_service which supersedes enable_service, disable_service,
#   disable_log_reason, update_forced_down.

list_services = copy.deepcopy(servicesv211.list_services)
# The ID of the service is a uuid, so v2.1 pattern does not apply.
list_services['response_body']['properties']['services']['items'][
    'properties']['id'] = {'type': 'string', 'format': 'uuid'}

update_service = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'service': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'binary': {'type': 'string'},
                    # disabled_reason can be null when status is enabled.
                    'disabled_reason': {'type': ['string', 'null']},
                    'host': {'type': 'string'},
                    'state': {'type': 'string'},
                    'status': {'type': 'string'},
                    'updated_at': parameter_types.date_time,
                    'zone': {'type': 'string'},
                    'forced_down': {'type': 'boolean'}
                },
                'additionalProperties': False,
                'required': ['id', 'binary', 'disabled_reason', 'host',
                             'state', 'status', 'updated_at', 'zone',
                             'forced_down']
            }
        },
        'additionalProperties': False,
        'required': ['service']
    }
}

# **** Schemas unchanged in microversion 2.53 since microversion 2.11 ****
# Note(felipemonteiro): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
enable_disable_service = copy.deepcopy(servicesv211.enable_disable_service)
update_forced_down = copy.deepcopy(servicesv211.update_forced_down)
disable_log_reason = copy.deepcopy(servicesv211.disable_log_reason)
