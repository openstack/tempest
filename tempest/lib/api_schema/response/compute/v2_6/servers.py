# Copyright 2016 IBM Corp.
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

from tempest.lib.api_schema.response.compute.v2_3 import servers

# NOTE: Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.3 ******
list_servers = copy.deepcopy(servers.list_servers)
get_server = copy.deepcopy(servers.get_server)
list_servers_detail = copy.deepcopy(servers.list_servers_detail)
update_server = copy.deepcopy(servers.update_server)
rebuild_server = copy.deepcopy(servers.rebuild_server)
rebuild_server_with_admin_pass = copy.deepcopy(
    servers.rebuild_server_with_admin_pass)
show_server_diagnostics = copy.deepcopy(servers.show_server_diagnostics)
attach_volume = copy.deepcopy(servers.attach_volume)
show_volume_attachment = copy.deepcopy(servers.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers.list_volume_attachments)

# NOTE: The consolidated remote console API got introduced with v2.6
# with bp/consolidate-console-api. See Nova commit 578bafeda
get_remote_consoles = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'remote_console': {
                'type': 'object',
                'properties': {
                    'protocol': {'enum': ['vnc', 'rdp', 'serial', 'spice']},
                    'type': {'enum': ['novnc', 'xvpvnc', 'rdp-html5',
                                      'spice-html5', 'serial']},
                    'url': {
                        'type': 'string',
                        'format': 'uri'
                    }
                },
                'additionalProperties': False,
                'required': ['protocol', 'type', 'url']
            }
        },
        'additionalProperties': False,
        'required': ['remote_console']
    }
}
