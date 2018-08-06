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

from tempest.lib.api_schema.response.compute.v2_36 import quotas as quotasv236

# Compute microversion 2.57:
# remove attributes in quota_set:
#    'injected_file_content_bytes',
#    'injected_file_path_bytes',
#    'injected_files'

remove_item_list = ['injected_file_content_bytes', 'injected_file_path_bytes',
                    'injected_files']

update_quota_set = copy.deepcopy(quotasv236.update_quota_set)
for item in remove_item_list:
    update_quota_set['response_body']['properties']['quota_set'][
        'properties'].pop(item)
    update_quota_set['response_body']['properties']['quota_set'][
        'required'].remove(item)

get_quota_set = copy.deepcopy(quotasv236.get_quota_set)
for item in remove_item_list:
    get_quota_set['response_body']['properties']['quota_set'][
        'properties'].pop(item)
    get_quota_set['response_body']['properties']['quota_set'][
        'required'].remove(item)

get_quota_set_details = copy.deepcopy(quotasv236.get_quota_set_details)
for item in remove_item_list:
    get_quota_set_details['response_body']['properties']['quota_set'][
        'properties'].pop(item)
    get_quota_set_details['response_body']['properties']['quota_set'][
        'required'].remove(item)

# NOTE(zhufl): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.1 ***
delete_quota = copy.deepcopy(quotasv236.delete_quota)
