# Copyright 2020 ZTE Corporation.  All rights reserved.
#
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

from tempest.lib.api_schema.response.compute.v2_13 import server_groups as \
    server_groupsv213

# Compute microversion 2.64:
# 1. change policies to policy in:
#   * GET /os-server-groups
#   * POST /os-server-groups
#   * GET /os-server-groups/{server_group_id}
# 2. add rules in:
#   * GET /os-server-groups
#   * POST /os-server-groups
#   * GET /os-server-groups/{server_group_id}
# 3. remove metadata from:
#   * GET /os-server-groups
#   * POST /os-server-groups
#   * GET /os-server-groups/{server_group_id}

common_server_group = copy.deepcopy(server_groupsv213.common_server_group)
common_server_group['properties']['policy'] = {'type': 'string'}
common_server_group['properties']['rules'] = {'type': 'object'}
common_server_group['properties'].pop('policies')
common_server_group['properties'].pop('metadata')
common_server_group['required'].append('policy')
common_server_group['required'].append('rules')
common_server_group['required'].remove('policies')
common_server_group['required'].remove('metadata')

create_show_server_group = copy.deepcopy(
    server_groupsv213.create_show_server_group)
create_show_server_group['response_body']['properties'][
    'server_group'] = common_server_group

list_server_groups = copy.deepcopy(server_groupsv213.list_server_groups)
list_server_groups['response_body']['properties']['server_groups'][
    'items'] = common_server_group

# NOTE(zhufl): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
delete_server_group = copy.deepcopy(server_groupsv213.delete_server_group)
