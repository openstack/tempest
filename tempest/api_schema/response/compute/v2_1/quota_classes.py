# Copyright 2014 IBM Corporation.
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

from tempest.api_schema.response.compute.v2_1 import quotas

# NOTE(mriedem): os-quota-class-sets responses are the same as os-quota-sets
# except for the key in the response body is quota_class_set instead of
# quota_set, so update this copy of the schema from os-quota-sets.
get_quota_class_set = copy.deepcopy(quotas.get_quota_set)
get_quota_class_set['response_body']['properties']['quota_class_set'] = (
    get_quota_class_set['response_body']['properties'].pop('quota_set'))
get_quota_class_set['response_body']['required'] = ['quota_class_set']

update_quota_class_set = copy.deepcopy(quotas.update_quota_set)
update_quota_class_set['response_body']['properties']['quota_class_set'] = (
    update_quota_class_set['response_body']['properties'].pop('quota_set'))
update_quota_class_set['response_body']['required'] = ['quota_class_set']
