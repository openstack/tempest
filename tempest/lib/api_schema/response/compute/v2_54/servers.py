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

from tempest.lib.api_schema.response.compute.v2_48 import servers as servers248
# ****** Schemas changed in microversion 2.54 *****************

# Note(gmann): This is schema for microversion 2.54 which includes the
# 'key_name' in the Response body of the following APIs:
#    - ``POST '/servers/{server_id}/action (rebuild)``

key_name = {
    'oneOf': [
        {'type': 'string', 'minLength': 1, 'maxLength': 255},
        {'type': 'null'},
    ]
}

rebuild_server = copy.deepcopy(servers248.rebuild_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].update({'key_name': key_name})
rebuild_server['response_body']['properties']['server'][
    'required'].append('key_name')

rebuild_server_with_admin_pass = copy.deepcopy(
    servers248.rebuild_server_with_admin_pass)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'key_name': key_name})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('key_name')

# NOTE(gmann): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged in microversion 2.54 since microversion 2.48 ***
get_server = copy.deepcopy(servers248.get_server)
list_servers_detail = copy.deepcopy(servers248.list_servers_detail)
update_server = copy.deepcopy(servers248.update_server)
list_servers = copy.deepcopy(servers248.list_servers)
show_server_diagnostics = copy.deepcopy(servers248.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers248.get_remote_consoles)
list_tags = copy.deepcopy(servers248.list_tags)
update_all_tags = copy.deepcopy(servers248.update_all_tags)
delete_all_tags = copy.deepcopy(servers248.delete_all_tags)
check_tag_existence = copy.deepcopy(servers248.check_tag_existence)
update_tag = copy.deepcopy(servers248.update_tag)
delete_tag = copy.deepcopy(servers248.delete_tag)
attach_volume = copy.deepcopy(servers248.attach_volume)
show_volume_attachment = copy.deepcopy(servers248.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers248.list_volume_attachments)
