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

from tempest.lib.api_schema.response.compute.v2_57 import servers as servers257
from tempest.lib.api_schema.response.compute.v2_73 import servers as servers273


###########################################################################
#
# 2.75:
#
# Server representation is made consistent among GET, PUT
# and Rebuild serevr APIs response.
#
###########################################################################

rebuild_server = copy.deepcopy(servers273.get_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].pop('OS-EXT-SRV-ATTR:user_data')
rebuild_server['status_code'] = [202]
rebuild_server['response_body']['properties']['server'][
    'properties'].update({'user_data': servers257.user_data})
rebuild_server['response_body']['properties']['server'][
    'required'].append('user_data')

rebuild_server_with_admin_pass = copy.deepcopy(rebuild_server)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'adminPass': {'type': 'string'}})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('adminPass')

update_server = copy.deepcopy(servers273.get_server)

# NOTE(gmann): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.73 ***
get_server = copy.deepcopy(servers273.get_server)
list_servers = copy.deepcopy(servers273.list_servers)
list_servers_detail = copy.deepcopy(servers273.list_servers_detail)
show_server_diagnostics = copy.deepcopy(servers273.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers273.get_remote_consoles)
list_tags = copy.deepcopy(servers273.list_tags)
update_all_tags = copy.deepcopy(servers273.update_all_tags)
delete_all_tags = copy.deepcopy(servers273.delete_all_tags)
check_tag_existence = copy.deepcopy(servers273.check_tag_existence)
update_tag = copy.deepcopy(servers273.update_tag)
delete_tag = copy.deepcopy(servers273.delete_tag)
attach_volume = copy.deepcopy(servers273.attach_volume)
show_volume_attachment = copy.deepcopy(servers273.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers273.list_volume_attachments)
show_instance_action = copy.deepcopy(servers273.show_instance_action)
create_backup = copy.deepcopy(servers273.create_backup)
