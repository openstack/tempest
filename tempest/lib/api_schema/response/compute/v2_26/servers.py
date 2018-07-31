# Copyright 2016 IBM Corp.
# Copyright 2017 AT&T Corp.
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

update_server = copy.deepcopy(servers219.update_server)
update_server['response_body']['properties']['server'][
    'properties'].update({'tags': tag_items})
update_server['response_body']['properties']['server'][
    'required'].append('tags')

rebuild_server = copy.deepcopy(servers219.rebuild_server)
rebuild_server['response_body']['properties']['server'][
    'properties'].update({'tags': tag_items})
rebuild_server['response_body']['properties']['server'][
    'required'].append('tags')

rebuild_server_with_admin_pass = copy.deepcopy(
    servers219.rebuild_server_with_admin_pass)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'tags': tag_items})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('tags')

list_tags = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'tags': tag_items,
        },
        'additionalProperties': False,
        'required': ['tags']
    }
}

update_all_tags = copy.deepcopy(list_tags)

delete_all_tags = {'status_code': [204]}

check_tag_existence = {'status_code': [204]}

update_tag = {
    'status_code': [201, 204],
    'response_header': {
        'type': 'object',
        'properties': {
            'location': {
                'type': 'string'
            }
        },
        'required': ['location']
    }
}

delete_tag = {'status_code': [204]}

# NOTE(gmann): Below are the unchanged schema in this microversion. We need
# to keep this schema in this file to have the generic way to select the
# right schema based on self.schema_versions_info mapping in service client.
# ****** Schemas unchanged since microversion 2.19 ******
list_servers = copy.deepcopy(servers219.list_servers)
show_server_diagnostics = copy.deepcopy(servers219.show_server_diagnostics)
get_remote_consoles = copy.deepcopy(servers219.get_remote_consoles)
