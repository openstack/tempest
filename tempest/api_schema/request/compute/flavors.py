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

common_flavor_details = {
    "name": "get-flavor-details",
    "http-method": "GET",
    "url": "flavors/%s",
    "resources": [
        {"name": "flavor", "expected_result": 404}
    ]
}

common_flavor_list = {
    "name": "list-flavors-with-detail",
    "http-method": "GET",
    "url": "flavors/detail",
    "json-schema": {
        "type": "object",
        "properties": {
        }
    }
}

common_admin_flavor_create = {
    "name": "flavor-create",
    "http-method": "POST",
    "admin_client": True,
    "url": "flavors",
    "default_result_code": 400,
    "json-schema": {
        "type": "object",
        "properties": {
           "flavor": {
               "type": "object",
               "properties": {
                   "name": {"type": "string",
                            "exclude_tests": ["gen_str_min_length"]},
                   "ram": {"type": "integer", "minimum": 1},
                   "vcpus": {"type": "integer", "minimum": 1},
                   "disk": {"type": "integer"},
                   "id": {"type": "integer",
                          "exclude_tests": ["gen_none", "gen_string"]
                          },
                   }
               }
        }
    }
}
