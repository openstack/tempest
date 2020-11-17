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

from tempest.lib.api_schema.response.compute.v2_1 import interfaces

# ****** Schemas changed in microversion 2.70 *****************
#
# 1. add optional field 'tag' in the Response body of the following APIs:
#    - GET /servers/{server_id}/os-interface
#    - POST /servers/{server_id}/os-interface
#    - GET /servers/{server_id}/os-interface/{port_id}

get_create_interfaces = copy.deepcopy(interfaces.get_create_interfaces)
get_create_interfaces['response_body']['properties']['interfaceAttachment'][
    'properties'].update({'tag': {'type': ['string', 'null']}})

list_interfaces = copy.deepcopy(interfaces.list_interfaces)
list_interfaces['response_body']['properties']['interfaceAttachments'][
    'items']['properties'].update({'tag': {'type': ['string', 'null']}})

# NOTE(zhufl): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.1 ***
delete_interface = copy.deepcopy(interfaces.delete_interface)
