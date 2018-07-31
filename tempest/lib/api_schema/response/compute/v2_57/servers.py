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

from tempest.lib.api_schema.response.compute.v2_54 import servers as servers254
# ****** Schemas changed in microversion 2.57 *****************

# Note(gmann): This is schema for microversion 2.57 which includes the
# 'user_data' in the Response body of the following APIs:
#    - ``POST '/servers/{server_id}/action (rebuild)``

user_data = {
    'oneOf': [
        {
            'type': 'string',
            'format': 'base64',
            'maxLength': 65535
        },
        {'type': 'null'}
    ]
}

rebuild_server = copy.deepcopy(servers254.rebuild_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].update({'user_data': user_data})
rebuild_server['response_body']['properties']['server'][
    'required'].append('user_data')

rebuild_server_with_admin_pass = copy.deepcopy(
    servers254.rebuild_server_with_admin_pass)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'user_data': user_data})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('user_data')

# NOTE(gmann): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged in microversion 2.57 since microversion 2.54 ***
get_server = copy.deepcopy(servers254.get_server)
list_servers_detail = copy.deepcopy(servers254.list_servers_detail)
update_server = copy.deepcopy(servers254.update_server)
list_servers = copy.deepcopy(servers254.list_servers)
show_server_diagnostics = copy.deepcopy(servers254.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers254.get_remote_consoles)
list_tags = copy.deepcopy(servers254.list_tags)
update_all_tags = copy.deepcopy(servers254.update_all_tags)
delete_all_tags = copy.deepcopy(servers254.delete_all_tags)
check_tag_existence = copy.deepcopy(servers254.check_tag_existence)
update_tag = copy.deepcopy(servers254.update_tag)
delete_tag = copy.deepcopy(servers254.delete_tag)
