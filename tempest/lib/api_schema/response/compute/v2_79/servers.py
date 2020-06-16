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

from tempest.lib.api_schema.response.compute.v2_73 import servers as servers273


###########################################################################
#
# 2.79:
#
# The delete_on_termination parameter is now returned in the response body
# of the following calls:
#
# - GET /servers/{server_id}/os-volume_attachments
# - GET /servers/{server_id}/os-volume_attachments/{volume_id}
# - POST /servers/{server_id}/os-volume_attachments
###########################################################################

attach_volume = copy.deepcopy(servers273.attach_volume)
attach_volume['response_body']['properties']['volumeAttachment'][
    'properties'].update({'delete_on_termination': {'type': 'boolean'}})
attach_volume['response_body']['properties']['volumeAttachment'][
    'required'].append('delete_on_termination')

show_volume_attachment = copy.deepcopy(servers273.show_volume_attachment)
show_volume_attachment['response_body']['properties']['volumeAttachment'][
    'properties'].update({'delete_on_termination': {'type': 'boolean'}})
show_volume_attachment['response_body']['properties'][
    'volumeAttachment']['required'].append('delete_on_termination')

list_volume_attachments = copy.deepcopy(servers273.list_volume_attachments)
list_volume_attachments['response_body']['properties']['volumeAttachments'][
    'items']['properties'].update(
        {'delete_on_termination': {'type': 'boolean'}})
list_volume_attachments['response_body']['properties'][
    'volumeAttachments']['items']['required'].append('delete_on_termination')

# NOTE(zhufl): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.73 ***
rebuild_server = copy.deepcopy(servers273.rebuild_server)
rebuild_server_with_admin_pass = copy.deepcopy(
    servers273.rebuild_server_with_admin_pass)
update_server = copy.deepcopy(servers273.update_server)
get_server = copy.deepcopy(servers273.get_server)
list_servers_detail = copy.deepcopy(servers273.list_servers_detail)
list_servers = copy.deepcopy(servers273.list_servers)
show_server_diagnostics = copy.deepcopy(servers273.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers273.get_remote_consoles)
list_tags = copy.deepcopy(servers273.list_tags)
update_all_tags = copy.deepcopy(servers273.update_all_tags)
delete_all_tags = copy.deepcopy(servers273.delete_all_tags)
check_tag_existence = copy.deepcopy(servers273.check_tag_existence)
update_tag = copy.deepcopy(servers273.update_tag)
delete_tag = copy.deepcopy(servers273.delete_tag)
