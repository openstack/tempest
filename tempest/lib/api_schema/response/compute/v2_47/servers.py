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

from tempest.lib.api_schema.response.compute.v2_26 import servers as servers226

flavor = {
    'type': 'object',
    'properties': {
        'original_name': {'type': 'string'},
        'disk': {'type': 'integer'},
        'ephemeral': {'type': 'integer'},
        'ram': {'type': 'integer'},
        'swap': {'type': 'integer'},
        'vcpus': {'type': 'integer'},
        'extra_specs': {
            'type': 'object',
            'patternProperties': {
                '^[a-zA-Z0-9_\-\. :]+$': {'type': 'string'}
            }
        }
    },
    'additionalProperties': False,
    'required': ['original_name', 'disk', 'ephemeral', 'ram', 'swap', 'vcpus']
}

get_server = copy.deepcopy(servers226.get_server)
get_server['response_body']['properties']['server'][
    'properties'].update({'flavor': flavor})
