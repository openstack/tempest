# Copyright 2018 ZTE Corporation.  All rights reserved.
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

from tempest.lib.api_schema.response.compute.v2_1 import aggregates

# 'uuid' of an aggregate is returned in microversion 2.41
aggregate_for_create = copy.deepcopy(aggregates.aggregate_for_create)
aggregate_for_create['properties'].update({'uuid': {'type': 'string',
                                                    'format': 'uuid'}})
aggregate_for_create['required'].append('uuid')

common_aggregate_info = copy.deepcopy(aggregates.common_aggregate_info)
common_aggregate_info['properties'].update({'uuid': {'type': 'string',
                                                     'format': 'uuid'}})
common_aggregate_info['required'].append('uuid')

list_aggregates = copy.deepcopy(aggregates.list_aggregates)
list_aggregates['response_body']['properties']['aggregates'].update(
    {'items': common_aggregate_info})

get_aggregate = copy.deepcopy(aggregates.get_aggregate)
get_aggregate['response_body']['properties'].update(
    {'aggregate': common_aggregate_info})

aggregate_set_metadata = get_aggregate

update_aggregate = copy.deepcopy(aggregates.update_aggregate)
update_aggregate['response_body']['properties'].update(
    {'aggregate': common_aggregate_info})

create_aggregate = copy.deepcopy(aggregates.create_aggregate)
create_aggregate['response_body']['properties'].update(
    {'aggregate': aggregate_for_create})

aggregate_add_remove_host = get_aggregate

# NOTE(zhufl): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.1 ***
delete_aggregate = copy.deepcopy(aggregates.delete_aggregate)
