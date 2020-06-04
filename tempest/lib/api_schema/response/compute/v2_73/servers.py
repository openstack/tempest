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

from tempest.lib.api_schema.response.compute.v2_71 import servers as servers271


###########################################################################
#
# 2.73:
#
# The locked_reason parameter is now returned in the response body of the
# following calls:
#
# - POST /servers/{server_id}/action (where the action is rebuild)
# - PUT /servers/{server_id} (update)
# - GET /servers/{server_id} (show)
# - GET /servers/detail (list)
#
###########################################################################

# The "locked_reason" parameter will either be a string or None.
locked_reason = {'type': ['string', 'null']}

rebuild_server = copy.deepcopy(servers271.rebuild_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].update({'locked_reason': locked_reason})
rebuild_server['response_body']['properties']['server'][
    'required'].append('locked_reason')

rebuild_server_with_admin_pass = copy.deepcopy(
    servers271.rebuild_server_with_admin_pass)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'locked_reason': locked_reason})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('locked_reason')

update_server = copy.deepcopy(servers271.update_server)
update_server['response_body']['properties']['server'][
    'properties'].update({'locked_reason': locked_reason})
update_server['response_body']['properties']['server'][
    'required'].append('locked_reason')

get_server = copy.deepcopy(servers271.get_server)
get_server['response_body']['properties']['server'][
    'properties'].update({'locked_reason': locked_reason})
get_server['response_body']['properties']['server'][
    'required'].append('locked_reason')

list_servers_detail = copy.deepcopy(servers271.list_servers_detail)
list_servers_detail['response_body']['properties']['servers']['items'][
    'properties'].update({'locked_reason': locked_reason})
list_servers_detail['response_body']['properties']['servers']['items'][
    'required'].append('locked_reason')

# NOTE(lajoskatona): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.71 ***
list_servers = copy.deepcopy(servers271.list_servers)
show_server_diagnostics = copy.deepcopy(servers271.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers271.get_remote_consoles)
list_tags = copy.deepcopy(servers271.list_tags)
update_all_tags = copy.deepcopy(servers271.update_all_tags)
delete_all_tags = copy.deepcopy(servers271.delete_all_tags)
check_tag_existence = copy.deepcopy(servers271.check_tag_existence)
update_tag = copy.deepcopy(servers271.update_tag)
delete_tag = copy.deepcopy(servers271.delete_tag)
attach_volume = copy.deepcopy(servers271.attach_volume)
show_volume_attachment = copy.deepcopy(servers271.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers271.list_volume_attachments)
