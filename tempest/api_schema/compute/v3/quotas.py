# Copyright 2014 NEC Corporation.  All rights reserved.
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

from tempest.api_schema.compute import quotas

quota_set = copy.deepcopy(quotas.common_quota_set)
quota_set['response_body']['properties']['quota_set']['properties'][
    'id'] = {'type': 'string'}
quota_set['response_body']['properties']['quota_set'][
    'required'].extend(['id'])

quota_common_info = {
    'type': 'object',
    'properties': {
        'reserved': {'type': 'integer'},
        'limit': {'type': 'integer'},
        'in_use': {'type': 'integer'}
    },
    'required': ['reserved', 'limit', 'in_use']
}

quota_set_detail = copy.deepcopy(quotas.common_quota_set)
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'id'] = {'type': 'string'}
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'instances'] = quota_common_info
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'cores'] = quota_common_info
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'ram'] = quota_common_info
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'floating_ips'] = quota_common_info
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'fixed_ips'] = quota_common_info
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'metadata_items'] = quota_common_info
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'key_pairs'] = quota_common_info
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'security_groups'] = quota_common_info
quota_set_detail['response_body']['properties']['quota_set']['properties'][
    'security_group_rules'] = quota_common_info

delete_quota = {
    'status_code': [204]
}
