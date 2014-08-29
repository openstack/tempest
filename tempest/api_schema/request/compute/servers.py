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

common_get_console_output = {
    "name": "get-console-output",
    "http-method": "POST",
    "url": "servers/%s/action",
    "resources": [
        {"name": "server", "expected_result": 404}
    ],
    "json-schema": {
        "type": "object",
        "properties": {
            "os-getConsoleOutput": {
                "type": "object",
                "properties": {
                    "length": {
                        "type": ["integer", "string"],
                        "minimum": 0
                    }
                }
            }
        },
        "additionalProperties": False
    }
}
