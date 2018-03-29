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

from tempest.lib.api_schema.response.compute.v2_39 import limits as limitv239

# Compute microversion 2.57:
# remove attributes in get_limit:
#    'maxPersonality',
#    'maxPersonalitySize'

get_limit = copy.deepcopy(limitv239.get_limit)

for item in ['maxPersonality', 'maxPersonalitySize']:
    get_limit['response_body']['properties']['limits']['properties'][
        'absolute']['properties'].pop(item)
    get_limit['response_body']['properties']['limits']['properties'][
        'absolute']['required'].remove(item)
