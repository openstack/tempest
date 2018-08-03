# Copyright 2018 AT&T Corporation.  All Rights Reserved.
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

from tempest.lib.api_schema.response.compute.v2_6 import servers

# 2.8: Add 'mks' protocol and 'webmks' type for remote consoles.
get_remote_consoles = copy.deepcopy(servers.get_remote_consoles)
get_remote_consoles['response_body']['properties']['remote_console'][
    'properties']['protocol']['enum'].append('mks')
get_remote_consoles['response_body']['properties']['remote_console'][
    'properties']['type']['enum'].append('webmks')

# NOTE: Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.6 ******
list_servers = copy.deepcopy(servers.list_servers)
get_server = copy.deepcopy(servers.get_server)
list_servers_detail = copy.deepcopy(servers.list_servers_detail)
update_server = copy.deepcopy(servers.update_server)
rebuild_server = copy.deepcopy(servers.rebuild_server)
rebuild_server_with_admin_pass = copy.deepcopy(
    servers.rebuild_server_with_admin_pass)
show_server_diagnostics = copy.deepcopy(servers.show_server_diagnostics)
