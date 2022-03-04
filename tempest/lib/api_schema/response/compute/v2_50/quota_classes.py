# All rights reserved.
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
from tempest.lib.api_schema.response.compute.v2_1 import quota_classes \
    as quota_classesv21

# Compute microversion 2.50:
# 1. fixed_ips, floating_ips, security_group_rules and security_groups
#    are removed from:
#      * GET /os-quota-class-sets/{id}
#      * PUT /os-quota-class-sets/{id}
# 2. server_groups and server_group_members are added to:
#      * GET /os-quota-class-sets/{id}
#      * PUT /os-quota-class-sets/{id}

get_quota_class_set = copy.deepcopy(quota_classesv21.get_quota_class_set)
update_quota_class_set = copy.deepcopy(quota_classesv21.update_quota_class_set)
for field in ['fixed_ips', 'floating_ips', 'security_group_rules',
              'security_groups']:
    get_quota_class_set['response_body']['properties']['quota_class_set'][
        'properties'].pop(field, None)
    get_quota_class_set['response_body']['properties']['quota_class_set'][
        'required'].remove(field)
    update_quota_class_set['response_body']['properties']['quota_class_set'][
        'properties'].pop(field, None)
    update_quota_class_set['response_body']['properties'][
        'quota_class_set']['required'].remove(field)
for field in ['server_groups', 'server_group_members']:
    get_quota_class_set['response_body']['properties']['quota_class_set'][
        'properties'].update({field: {'type': 'integer'}})
    get_quota_class_set['response_body']['properties']['quota_class_set'][
        'required'].append(field)
    update_quota_class_set['response_body']['properties']['quota_class_set'][
        'properties'].update({field: {'type': 'integer'}})
    update_quota_class_set['response_body']['properties']['quota_class_set'][
        'required'].append(field)
