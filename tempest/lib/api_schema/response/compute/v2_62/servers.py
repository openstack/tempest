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

from tempest.lib.api_schema.response.compute.v2_58 import servers as servers258

# microversion 2.62 added hostId and host to the event, but only hostId is
# mandatory
show_instance_action = copy.deepcopy(servers258.show_instance_action)
show_instance_action['response_body']['properties']['instanceAction'][
    'properties']['events']['items'][
    'properties']['hostId'] = {'type': 'string'}
show_instance_action['response_body']['properties']['instanceAction'][
    'properties']['events']['items']['properties']['host'] = {'type': 'string'}
show_instance_action['response_body']['properties']['instanceAction'][
    'properties']['events']['items']['required'].append('hostId')

# Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
list_servers = copy.deepcopy(servers258.list_servers)
show_server_diagnostics = copy.deepcopy(servers258.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers258.get_remote_consoles)
list_tags = copy.deepcopy(servers258.list_tags)
update_all_tags = copy.deepcopy(servers258.update_all_tags)
delete_all_tags = copy.deepcopy(servers258.delete_all_tags)
check_tag_existence = copy.deepcopy(servers258.check_tag_existence)
update_tag = copy.deepcopy(servers258.update_tag)
delete_tag = copy.deepcopy(servers258.delete_tag)
get_server = copy.deepcopy(servers258.get_server)
list_servers_detail = copy.deepcopy(servers258.list_servers_detail)
update_server = copy.deepcopy(servers258.update_server)
rebuild_server = copy.deepcopy(servers258.rebuild_server)
rebuild_server_with_admin_pass = copy.deepcopy(
    servers258.rebuild_server_with_admin_pass)
attach_volume = copy.deepcopy(servers258.attach_volume)
show_volume_attachment = copy.deepcopy(servers258.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers258.list_volume_attachments)
create_backup = copy.deepcopy(servers258.create_backup)
