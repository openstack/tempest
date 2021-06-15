# Copyright 2020 ZTE Corporation.  All rights reserved.
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

from tempest.lib.api_schema.response.volume import services

# Volume microversion 3.7:
# 1. New optional attribute in 'services' dict.
#      'cluster'

list_services = copy.deepcopy(services.list_services)
list_services['response_body']['properties']['services']['items'][
    'properties'].update({'cluster': {'type': ['string', 'null']}})

# NOTE(zhufl): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 3.0 ******
enable_service = copy.deepcopy(services.enable_service)
disable_service = copy.deepcopy(services.disable_service)
disable_log_reason = copy.deepcopy(services.disable_log_reason)
freeze_host = copy.deepcopy(services.freeze_host)
thaw_host = copy.deepcopy(services.thaw_host)
