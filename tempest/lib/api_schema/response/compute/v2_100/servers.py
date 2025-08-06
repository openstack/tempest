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

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types
from tempest.lib.api_schema.response.compute.v2_99 import servers as servers299

###########################################################################
#
# 2.100:
#
# The scheduler_hints parameter is now returned in the response body
# of the following calls:
# - GET /servers/detail
# - GET /servers/{server_id}
# - POST /server/{server_id}/action (rebuild)
# - PUT /servers/{server_id}
#
###########################################################################

_hints = {
    'type': 'object',
    'properties': {
        'group': {
            'type': 'string',
            'format': 'uuid'
        },
        'different_host': {
            # NOTE: The value of 'different_host' is the set of server
            # uuids where a new server is scheduled on a different host.
            # A user can specify one server as string parameter and should
            # specify multiple servers as array parameter instead.
            'oneOf': [
                {
                    'type': 'string',
                    'format': 'uuid'
                },
                {
                    'type': 'array',
                    'items': parameter_types.server_id
                }
            ]
        },
        'same_host': {
            # NOTE: The value of 'same_host' is the set of server
            # uuids where a new server is scheduled on the same host.
            'type': ['string', 'array'],
            'items': parameter_types.server_id
        },
        'query': {
            # NOTE: The value of 'query' is converted to dict data with
            # jsonutils.loads() and used for filtering hosts.
            'type': ['string', 'object'],
        },
        # NOTE: The value of 'target_cell' is the cell name what cell
        # a new server is scheduled on.
        'target_cell': parameter_types.name,
        'different_cell': {
            'type': ['string', 'array'],
            'items': {
                'type': 'string'
            }
        },
        'build_near_host_ip': parameter_types.ip_address,
        'cidr': {
            'type': 'string',
            'pattern': '^/[0-9a-f.:]+$'
        },
    },
    # NOTE: As this Mail:
    # http://lists.openstack.org/pipermail/openstack-dev/2015-June/067996.html
    # pointed out the limit the scheduler-hints in the API is problematic. So
    # relax it.
    'additionalProperties': True
}

get_server = copy.deepcopy(servers299.get_server)
get_server['response_body']['properties']['server'][
    'properties'].update({'scheduler_hints': _hints})
get_server['response_body']['properties']['server'][
    'required'].append('scheduler_hints')

list_servers_detail = copy.deepcopy(servers299.list_servers_detail)
list_servers_detail['response_body']['properties']['servers']['items'][
    'properties'].update({'scheduler_hints': _hints})
list_servers_detail['response_body']['properties']['servers']['items'][
    'required'].append('scheduler_hints')

rebuild_server = copy.deepcopy(servers299.rebuild_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].update({'scheduler_hints': _hints})
rebuild_server['response_body']['properties']['server'][
    'required'].append('scheduler_hints')

rebuild_server_with_admin_pass = copy.deepcopy(
    servers299.rebuild_server_with_admin_pass)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'scheduler_hints': _hints})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('scheduler_hints')

update_server = copy.deepcopy(servers299.update_server)
update_server['response_body']['properties']['server'][
    'properties'].update({'scheduler_hints': _hints})
update_server['response_body']['properties']['server'][
    'required'].append('scheduler_hints')

# NOTE(zhufl): Below are the unchanged schema in this microversion. We
# need to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.99***
attach_volume = copy.deepcopy(servers299.attach_volume)
show_volume_attachment = copy.deepcopy(servers299.show_volume_attachment)
list_volume_attachments = copy.deepcopy(servers299.list_volume_attachments)
list_servers = copy.deepcopy(servers299.list_servers)
show_server_diagnostics = copy.deepcopy(servers299.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers299.get_remote_consoles)
show_instance_action = copy.deepcopy(servers299.show_instance_action)
create_backup = copy.deepcopy(servers299.create_backup)
list_live_migrations = copy.deepcopy(servers299.list_live_migrations)
