# Copyright 2017 NTT Corporation.  All rights reserved.
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

from tempest.lib.api_schema.response.compute.v2_1 import server_groups

# Compute microversion 2.13:
# 1. New attributes in 'server_group' dict.
#      'project_id', 'user_id'
common_server_group = copy.deepcopy(server_groups.common_server_group)
common_server_group['properties']['project_id'] = {'type': 'string'}
common_server_group['properties']['user_id'] = {'type': 'string'}
common_server_group['required'].append('project_id')
common_server_group['required'].append('user_id')

create_show_server_group = copy.deepcopy(
    server_groups.create_show_server_group)
create_show_server_group['response_body']['properties'][
    'server_group'] = common_server_group

delete_server_group = copy.deepcopy(server_groups.delete_server_group)

list_server_groups = copy.deepcopy(server_groups.list_server_groups)
list_server_groups['response_body']['properties']['server_groups'][
    'items'] = common_server_group
