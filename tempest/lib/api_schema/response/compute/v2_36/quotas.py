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

from tempest.lib.api_schema.response.compute.v2_1 import quotas as quotasv21

# Compute microversion 2.36:
# remove attributes in quota_set:
#    'fixed_ips',
#    'floating_ips',
#    'security_group_rules',
#    'security_groups'

remove_item_list = ['fixed_ips', 'floating_ips',
                    'security_group_rules', 'security_groups']

update_quota_set = copy.deepcopy(quotasv21.update_quota_set)
for item in remove_item_list:
    update_quota_set['response_body']['properties']['quota_set'][
        'properties'].pop(item)
    update_quota_set['response_body']['properties']['quota_set'][
        'required'].remove(item)

get_quota_set = copy.deepcopy(quotasv21.get_quota_set)
for item in remove_item_list:
    get_quota_set['response_body']['properties']['quota_set'][
        'properties'].pop(item)
    get_quota_set['response_body']['properties']['quota_set'][
        'required'].remove(item)

get_quota_set_details = copy.deepcopy(quotasv21.get_quota_set_details)
for item in remove_item_list:
    get_quota_set_details['response_body']['properties']['quota_set'][
        'properties'].pop(item)
    get_quota_set_details['response_body']['properties']['quota_set'][
        'required'].remove(item)

# NOTE(zhufl): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.1 ***
delete_quota = copy.deepcopy(quotasv21.delete_quota)
