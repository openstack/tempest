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
from tempest.lib.api_schema.response.compute.v2_57 import servers as servers257

# microversion 2.58 added updated_at to the response
show_instance_action = copy.deepcopy(servers257.show_instance_action)
show_instance_action['response_body']['properties']['instanceAction'][
    'properties']['updated_at'] = parameter_types.date_time
show_instance_action['response_body']['properties']['instanceAction'][
    'required'].append('updated_at')

# Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
list_servers = copy.deepcopy(servers257.list_servers)
show_server_diagnostics = copy.deepcopy(servers257.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers257.get_remote_consoles)
list_tags = copy.deepcopy(servers257.list_tags)
update_all_tags = copy.deepcopy(servers257.update_all_tags)
delete_all_tags = copy.deepcopy(servers257.delete_all_tags)
check_tag_existence = copy.deepcopy(servers257.check_tag_existence)
update_tag = copy.deepcopy(servers257.update_tag)
delete_tag = copy.deepcopy(servers257.delete_tag)
get_server = copy.deepcopy(servers257.get_server)
list_servers_detail = copy.deepcopy(servers257.list_servers_detail)
update_server = copy.deepcopy(servers257.update_server)
rebuild_server = copy.deepcopy(servers257.rebuild_server)
rebuild_server_with_admin_pass = copy.deepcopy(
    servers257.rebuild_server_with_admin_pass)
attach_volume = copy.deepcopy(servers257.attach_volume)
show_volume_attachment = copy.deepcopy(servers257.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers257.list_volume_attachments)
create_backup = copy.deepcopy(servers257.create_backup)
