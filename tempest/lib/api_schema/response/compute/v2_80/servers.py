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

from tempest.lib.api_schema.response.compute.v2_79 import servers as servers279

###########################################################################
#
# 2.80:
#
# The user_id and project_id value is now returned in the response body in
# addition to the migration id for the following API responses:
#
# - GET /os-migrations
#
###########################################################################

list_live_migrations = copy.deepcopy(servers279.list_live_migrations)
list_live_migrations['response_body']['properties']['migrations']['items'][
    'properties'].update({
        'user_id': {'type': 'string'},
        'project_id': {'type': 'string'}
    })
list_live_migrations['response_body']['properties']['migrations']['items'][
    'required'].extend(['user_id', 'project_id'])

# NOTE(zhufl): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.79 ***
rebuild_server = copy.deepcopy(servers279.rebuild_server)
rebuild_server_with_admin_pass = copy.deepcopy(
    servers279.rebuild_server_with_admin_pass)
update_server = copy.deepcopy(servers279.update_server)
get_server = copy.deepcopy(servers279.get_server)
list_servers_detail = copy.deepcopy(servers279.list_servers_detail)
list_servers = copy.deepcopy(servers279.list_servers)
show_server_diagnostics = copy.deepcopy(servers279.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers279.get_remote_consoles)
list_tags = copy.deepcopy(servers279.list_tags)
update_all_tags = copy.deepcopy(servers279.update_all_tags)
delete_all_tags = copy.deepcopy(servers279.delete_all_tags)
check_tag_existence = copy.deepcopy(servers279.check_tag_existence)
update_tag = copy.deepcopy(servers279.update_tag)
delete_tag = copy.deepcopy(servers279.delete_tag)
show_instance_action = copy.deepcopy(servers279.show_instance_action)
create_backup = copy.deepcopy(servers279.create_backup)
attach_volume = copy.deepcopy(servers279.attach_volume)
show_volume_attachment = copy.deepcopy(servers279.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers279.list_volume_attachments)
