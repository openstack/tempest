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

from tempest.api_schema.compute import interfaces as common_schema

list_interfaces = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'interface_attachments': {
                'type': 'array',
                'items': common_schema.interface_common_info
            }
        },
        'required': ['interface_attachments']
    }
}
