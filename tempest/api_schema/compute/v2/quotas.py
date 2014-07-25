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
quota_set['response_body']['properties']['quota_set']['properties'][
    'injected_files'] = {'type': 'integer'}
quota_set['response_body']['properties']['quota_set']['properties'][
    'injected_file_content_bytes'] = {'type': 'integer'}
quota_set['response_body']['properties']['quota_set']['properties'][
    'injected_file_path_bytes'] = {'type': 'integer'}
quota_set['response_body']['properties']['quota_set']['required'].extend([
    'id',
    'injected_files',
    'injected_file_content_bytes',
    'injected_file_path_bytes'])

quota_set_update = copy.deepcopy(quotas.common_quota_set)
quota_set_update['response_body']['properties']['quota_set']['properties'][
    'injected_files'] = {'type': 'integer'}
quota_set_update['response_body']['properties']['quota_set']['properties'][
    'injected_file_content_bytes'] = {'type': 'integer'}
quota_set_update['response_body']['properties']['quota_set']['properties'][
    'injected_file_path_bytes'] = {'type': 'integer'}
quota_set_update['response_body']['properties']['quota_set'][
    'required'].extend(['injected_files',
                        'injected_file_content_bytes',
                        'injected_file_path_bytes'])

delete_quota = {
    'status_code': [202]
}
