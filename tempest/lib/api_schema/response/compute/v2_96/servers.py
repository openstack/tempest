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

from tempest.lib.api_schema.response.compute.v2_89 import servers as servers289


###########################################################################
#
# 2.96:
#
# The attachment_id and bdm_uuid parameter is now returned in the response body
# of the following calls:
# The pinned_availability_zone parameter is now returned in the response body
# of the following calls:
#
# - GET /servers/detail
# - GET /servers/{server_id}
# - PUT /servers/{server_id}
# - POST /servers/{server_id}/action (rebuild)
###########################################################################

get_server = copy.deepcopy(servers289.get_server)
get_server['response_body']['properties']['server'][
    'properties'].update(
        {'pinned_availability_zone': {'type': ['string', 'null']}})
get_server['response_body']['properties']['server'][
    'required'].append('pinned_availability_zone')

list_servers_detail = copy.deepcopy(servers289.list_servers_detail)
list_servers_detail['response_body']['properties']['servers']['items'][
    'properties'].update(
        {'pinned_availability_zone': {'type': ['string', 'null']}})
list_servers_detail['response_body']['properties']['servers']['items'][
    'required'].append('pinned_availability_zone')

update_server = copy.deepcopy(servers289.update_server)
update_server['response_body']['properties']['server'][
    'properties'].update(
        {'pinned_availability_zone': {'type': ['string', 'null']}})
update_server['response_body']['properties']['server'][
    'required'].append('pinned_availability_zone')

rebuild_server = copy.deepcopy(servers289.rebuild_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].update(
        {'pinned_availability_zone': {'type': ['string', 'null']}})
rebuild_server['response_body']['properties']['server'][
    'required'].append('pinned_availability_zone')

rebuild_server_with_admin_pass = copy.deepcopy(
    servers289.rebuild_server_with_admin_pass)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update(
        {'pinned_availability_zone': {'type': ['string', 'null']}})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('pinned_availability_zone')

# NOTE(zhufl): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.89***
attach_volume = copy.deepcopy(servers289.attach_volume)
show_volume_attachment = copy.deepcopy(servers289.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers289.list_volume_attachments)
list_servers = copy.deepcopy(servers289.list_servers)
show_server_diagnostics = copy.deepcopy(servers289.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers289.get_remote_consoles)
list_tags = copy.deepcopy(servers289.list_tags)
update_all_tags = copy.deepcopy(servers289.update_all_tags)
delete_all_tags = copy.deepcopy(servers289.delete_all_tags)
check_tag_existence = copy.deepcopy(servers289.check_tag_existence)
update_tag = copy.deepcopy(servers289.update_tag)
delete_tag = copy.deepcopy(servers289.delete_tag)
show_instance_action = copy.deepcopy(servers289.show_instance_action)
create_backup = copy.deepcopy(servers289.create_backup)
list_live_migrations = copy.deepcopy(servers289.list_live_migrations)
