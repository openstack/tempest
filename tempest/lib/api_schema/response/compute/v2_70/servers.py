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

from tempest.lib.api_schema.response.compute.v2_1 import servers as servers2_1
from tempest.lib.api_schema.response.compute.v2_63 import servers as servers263


###########################################################################
#
# 2.70:
#
# Exposes virtual device tags for volume attachments and virtual interfaces
# (ports). A tag parameter is added to the response body for the following
# APIs:
#
# Volumes
#
# - GET /servers/{server_id}/os-volume_attachments (list)
# - GET /servers/{server_id}/os-volume_attachments/{volume_id} (show)
# - POST /servers/{server_id}/os-volume_attachments (attach)
#
# Ports
#
# - GET /servers/{server_id}/os-interface (list)
# - GET /servers/{server_id}/os-interface/{port_id} (show)
# - POST /servers/{server_id}/os-interface (attach)
#
###########################################################################

attach_volume = copy.deepcopy(servers2_1.attach_volume)
attach_volume['response_body']['properties']['volumeAttachment'][
    'properties'].update({'tag': {'type': ['string', 'null']}})
attach_volume['response_body']['properties']['volumeAttachment'][
    'required'].append('tag')

show_volume_attachment = copy.deepcopy(servers2_1.show_volume_attachment)
show_volume_attachment['response_body']['properties']['volumeAttachment'][
    'properties'].update({'tag': {'type': ['string', 'null']}})
show_volume_attachment['response_body']['properties'][
    'volumeAttachment']['required'].append('tag')

list_volume_attachments = copy.deepcopy(servers2_1.list_volume_attachments)
list_volume_attachments['response_body']['properties']['volumeAttachments'][
    'items']['properties'].update({'tag': {'type': ['string', 'null']}})
list_volume_attachments['response_body']['properties'][
    'volumeAttachments']['items']['required'].append('tag')

# TODO(mriedem): Handle the os-interface changes when there is a test that
# needs them from this microversion onward.

# NOTE(lajoskatona): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.63 ***
list_servers_detail = copy.deepcopy(servers263.list_servers_detail)
rebuild_server = copy.deepcopy(servers263.rebuild_server)
rebuild_server_with_admin_pass = copy.deepcopy(
    servers263.rebuild_server_with_admin_pass)
update_server = copy.deepcopy(servers263.update_server)
get_server = copy.deepcopy(servers263.get_server)
list_servers = copy.deepcopy(servers263.list_servers)
show_server_diagnostics = copy.deepcopy(servers263.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers263.get_remote_consoles)
list_tags = copy.deepcopy(servers263.list_tags)
update_all_tags = copy.deepcopy(servers263.update_all_tags)
delete_all_tags = copy.deepcopy(servers263.delete_all_tags)
check_tag_existence = copy.deepcopy(servers263.check_tag_existence)
update_tag = copy.deepcopy(servers263.update_tag)
delete_tag = copy.deepcopy(servers263.delete_tag)
