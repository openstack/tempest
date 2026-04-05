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

from tempest.lib.api_schema.response.compute.v2_80 import servers as servers280

# microversion 2.84 added details to events in the response
show_instance_action = copy.deepcopy(servers280.show_instance_action)
show_instance_action['response_body']['properties']['instanceAction'][
    'properties']['events']['items']['properties'][
    'details'] = {'type': ['string', 'null']}

# Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
rebuild_server = copy.deepcopy(servers280.rebuild_server)
rebuild_server_with_admin_pass = copy.deepcopy(
    servers280.rebuild_server_with_admin_pass)
update_server = copy.deepcopy(servers280.update_server)
get_server = copy.deepcopy(servers280.get_server)
list_servers_detail = copy.deepcopy(servers280.list_servers_detail)
list_servers = copy.deepcopy(servers280.list_servers)
show_server_diagnostics = copy.deepcopy(servers280.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers280.get_remote_consoles)
list_tags = copy.deepcopy(servers280.list_tags)
update_all_tags = copy.deepcopy(servers280.update_all_tags)
delete_all_tags = copy.deepcopy(servers280.delete_all_tags)
check_tag_existence = copy.deepcopy(servers280.check_tag_existence)
update_tag = copy.deepcopy(servers280.update_tag)
delete_tag = copy.deepcopy(servers280.delete_tag)
list_instance_actions = copy.deepcopy(servers280.list_instance_actions)
create_backup = copy.deepcopy(servers280.create_backup)
attach_volume = copy.deepcopy(servers280.attach_volume)
show_volume_attachment = copy.deepcopy(servers280.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers280.list_volume_attachments)
list_live_migrations = copy.deepcopy(servers280.list_live_migrations)
