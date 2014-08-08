# (c) 2014 Deutsche Telekom AG
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import copy

from tempest.api_schema.request.compute import flavors

flavors_details = copy.deepcopy(flavors.common_flavor_details)

flavor_list = copy.deepcopy(flavors.common_flavor_list)

flavor_create = copy.deepcopy(flavors.common_admin_flavor_create)

flavor_list["json-schema"]["properties"] = {
    "minRam": {
        "type": "integer",
        "results": {
            "gen_none": 400,
            "gen_string": 400
        }
    },
    "minDisk": {
        "type": "integer",
        "results": {
            "gen_none": 400,
            "gen_string": 400
        }
    }
}
