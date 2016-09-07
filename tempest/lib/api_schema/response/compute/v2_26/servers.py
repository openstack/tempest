# Copyright 2016 IBM Corp.
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

from tempest.lib.api_schema.response.compute.v2_1 import servers as servers21
from tempest.lib.api_schema.response.compute.v2_19 import servers as servers219

# The 2.26 microversion changes the server GET and (detailed) LIST responses to
# include the server 'tags' which is just a list of strings.

tag_items = {
    'type': 'array',
    'maxItems': 50,
    'items': {
        'type': 'string',
        'pattern': '^[^,/]*$',
        'maxLength': 60
    }
}

get_server = copy.deepcopy(servers219.get_server)
get_server['response_body']['properties']['server'][
    'properties'].update({'tags': tag_items})
get_server['response_body']['properties']['server'][
    'required'].append('tags')

list_servers_detail = copy.deepcopy(servers219.list_servers_detail)
list_servers_detail['response_body']['properties']['servers']['items'][
    'properties'].update({'tags': tag_items})
list_servers_detail['response_body']['properties']['servers']['items'][
    'required'].append('tags')

# list response schema wasn't changed for v2.26 so use v2.1

list_servers = copy.deepcopy(servers21.list_servers)
