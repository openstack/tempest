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

from tempest.lib.api_schema.response.compute.v2_70 import servers as servers270


###########################################################################
#
# 2.71:
#
# The server_groups parameter will be in the response body of the following
# APIs to list the server groups to which the server belongs:
#
# - GET /servers/{server_id} (show)
# - PUT /servers/{server_id} (update)
# - POST /servers/{server_id}/action (rebuild)
#
###########################################################################

# The "server_groups" parameter will always be present and contain at most one
# UUID entry.
server_groups = {
    'type': 'array',
    'minItems': 0,
    'maxItems': 1,
    'items': {
        'type': 'string',
        'format': 'uuid'
    }
}

rebuild_server = copy.deepcopy(servers270.rebuild_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].update({'server_groups': server_groups})
rebuild_server['response_body']['properties']['server'][
    'required'].append('server_groups')

rebuild_server_with_admin_pass = copy.deepcopy(
    servers270.rebuild_server_with_admin_pass)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'server_groups': server_groups})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('server_groups')

update_server = copy.deepcopy(servers270.update_server)
update_server['response_body']['properties']['server'][
    'properties'].update({'server_groups': server_groups})
update_server['response_body']['properties']['server'][
    'required'].append('server_groups')

get_server = copy.deepcopy(servers270.get_server)
get_server['response_body']['properties']['server'][
    'properties'].update({'server_groups': server_groups})
get_server['response_body']['properties']['server'][
    'required'].append('server_groups')

# NOTE(lajoskatona): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.70 ***
list_servers_detail = copy.deepcopy(servers270.list_servers_detail)
list_servers = copy.deepcopy(servers270.list_servers)
show_server_diagnostics = copy.deepcopy(servers270.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers270.get_remote_consoles)
list_tags = copy.deepcopy(servers270.list_tags)
update_all_tags = copy.deepcopy(servers270.update_all_tags)
delete_all_tags = copy.deepcopy(servers270.delete_all_tags)
check_tag_existence = copy.deepcopy(servers270.check_tag_existence)
update_tag = copy.deepcopy(servers270.update_tag)
delete_tag = copy.deepcopy(servers270.delete_tag)
attach_volume = copy.deepcopy(servers270.attach_volume)
show_volume_attachment = copy.deepcopy(servers270.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers270.list_volume_attachments)
