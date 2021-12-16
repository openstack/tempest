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

from tempest.lib.api_schema.response.compute.v2_26 import servers as servers226
from tempest.lib.api_schema.response.compute.v2_45 import servers as servers245

flavor = {
    'type': 'object',
    'properties': {
        'original_name': {'type': 'string'},
        'disk': {'type': 'integer'},
        'ephemeral': {'type': 'integer'},
        'ram': {'type': 'integer'},
        'swap': {'type': 'integer'},
        'vcpus': {'type': 'integer'},
        'extra_specs': {
            'type': 'object',
            'patternProperties': {
                r'^[a-zA-Z0-9_\-\. :]+$': {'type': 'string'}
            }
        }
    },
    'additionalProperties': False,
    'required': ['original_name', 'disk', 'ephemeral', 'ram', 'swap', 'vcpus']
}

get_server = copy.deepcopy(servers245.get_server)
get_server['response_body']['properties']['server'][
    'properties'].update({'flavor': flavor})
list_servers_detail = copy.deepcopy(servers245.list_servers_detail)
list_servers_detail['response_body']['properties']['servers']['items'][
    'properties'].update({'flavor': flavor})

update_server = copy.deepcopy(servers245.update_server)
update_server['response_body']['properties']['server'][
    'properties'].update({'flavor': flavor})

rebuild_server = copy.deepcopy(servers245.rebuild_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].update({'flavor': flavor})

rebuild_server_with_admin_pass = copy.deepcopy(
    servers245.rebuild_server_with_admin_pass)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'flavor': flavor})

# NOTE(zhufl): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
show_server_diagnostics = copy.deepcopy(servers245.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers245.get_remote_consoles)
list_tags = copy.deepcopy(servers245.list_tags)
update_all_tags = copy.deepcopy(servers245.update_all_tags)
delete_all_tags = copy.deepcopy(servers245.delete_all_tags)
check_tag_existence = copy.deepcopy(servers245.check_tag_existence)
update_tag = copy.deepcopy(servers245.update_tag)
delete_tag = copy.deepcopy(servers245.delete_tag)
list_servers = copy.deepcopy(servers245.list_servers)
attach_volume = copy.deepcopy(servers245.attach_volume)
show_volume_attachment = copy.deepcopy(servers245.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers245.list_volume_attachments)
show_instance_action = copy.deepcopy(servers226.show_instance_action)
create_backup = copy.deepcopy(servers245.create_backup)
