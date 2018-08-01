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

# Nova microversion 2.63 adds 'trusted_image_certificates' (a list of
# certificate IDs) to the server rebuild and servers details responses.


trusted_certs = {
    'type': ['array', 'null'],
    'minItems': 1,
    'maxItems': 50,
    'uniqueItems': True,
    'items': {
        'type': 'string',
        'minLength': 1
    }
}

list_servers_detail = copy.deepcopy(servers257.list_servers_detail)
list_servers_detail['response_body']['properties']['servers']['items'][
    'properties'].update({'trusted_image_certificates': trusted_certs})
list_servers_detail['response_body']['properties']['servers']['items'][
    'required'].append('trusted_image_certificates')

rebuild_server = copy.deepcopy(servers257.rebuild_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].update({'trusted_image_certificates': trusted_certs})
rebuild_server['response_body']['properties']['server'][
    'required'].append('trusted_image_certificates')

rebuild_server_with_admin_pass = copy.deepcopy(
    servers257.rebuild_server_with_admin_pass)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'trusted_image_certificates': trusted_certs})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('trusted_image_certificates')

update_server = copy.deepcopy(servers257.update_server)
update_server['response_body']['properties']['server'][
    'properties'].update({'trusted_image_certificates': trusted_certs})
update_server['response_body']['properties']['server'][
    'required'].append('trusted_image_certificates')

get_server = copy.deepcopy(servers257.get_server)
get_server['response_body']['properties']['server'][
    'properties'].update({'trusted_image_certificates': trusted_certs})
get_server['response_body']['properties']['server'][
    'required'].append('trusted_image_certificates')

# NOTE(zhufl): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.57 ***
list_servers = copy.deepcopy(servers257.list_servers)
show_server_diagnostics = copy.deepcopy(servers257.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers257.get_remote_consoles)
list_tags = copy.deepcopy(servers257.list_tags)
update_all_tags = copy.deepcopy(servers257.update_all_tags)
delete_all_tags = copy.deepcopy(servers257.delete_all_tags)
check_tag_existence = copy.deepcopy(servers257.check_tag_existence)
update_tag = copy.deepcopy(servers257.update_tag)
delete_tag = copy.deepcopy(servers257.delete_tag)
