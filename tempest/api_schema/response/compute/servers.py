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

from tempest.api_schema.response.compute import parameter_types

get_password = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'password': {'type': 'string'}
        },
        'required': ['password']
    }
}

get_vnc_console = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'console': {
                'type': 'object',
                'properties': {
                    'type': {'type': 'string'},
                    'url': {
                        'type': 'string',
                        'format': 'uri'
                    }
                },
                'required': ['type', 'url']
            }
        },
        'required': ['console']
    }
}

common_show_server = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'name': {'type': 'string'},
        'status': {'type': 'string'},
        'image': {'oneOf': [
            {'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'links': parameter_types.links
                },
                'required': ['id', 'links']},
            {'type': ['string', 'null']}
        ]},
        'flavor': {
            'type': 'object',
            'properties': {
                'id': {'type': 'string'},
                'links': parameter_types.links
            },
            'required': ['id', 'links']
        },
        'fault': {
            'type': 'object',
            'properties': {
                'code': {'type': 'integer'},
                'created': {'type': 'string'},
                'message': {'type': 'string'},
                'details': {'type': 'string'},
            },
            # NOTE(gmann): 'details' is not necessary to be present
            #  in the 'fault'. So it is not defined as 'required'.
            'required': ['code', 'created', 'message']
        },
        'user_id': {'type': 'string'},
        'tenant_id': {'type': 'string'},
        'created': {'type': 'string'},
        'updated': {'type': 'string'},
        'progress': {'type': 'integer'},
        'metadata': {'type': 'object'},
        'links': parameter_types.links,
        'addresses': parameter_types.addresses,
    },
    # NOTE(GMann): 'progress' attribute is present in the response
    # only when server's status is one of the progress statuses
    # ("ACTIVE","BUILD", "REBUILD", "RESIZE","VERIFY_RESIZE")
    # 'fault' attribute is present in the response
    # only when server's status is one of the  "ERROR", "DELETED".
    # So they are not defined as 'required'.
    'required': ['id', 'name', 'status', 'image', 'flavor',
                 'user_id', 'tenant_id', 'created', 'updated',
                 'metadata', 'links', 'addresses']
}

base_update_get_server = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server': common_show_server
        },
        'required': ['server']
    }
}

delete_server = {
    'status_code': [204],
}

set_server_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'metadata': {
                'type': 'object',
                'patternProperties': {
                    '^.+$': {'type': 'string'}
                }
            }
        },
        'required': ['metadata']
    }
}

list_server_metadata = copy.deepcopy(set_server_metadata)

update_server_metadata = copy.deepcopy(set_server_metadata)

delete_server_metadata_item = {
    'status_code': [204]
}

list_servers = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'servers': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string'},
                        'links': parameter_types.links,
                        'name': {'type': 'string'}
                    },
                    'required': ['id', 'links', 'name']
                }
            },
            'servers_links': parameter_types.links
        },
        # NOTE(gmann): servers_links attribute is not necessary to be
        # present always So it is not 'required'.
        'required': ['servers']
    }
}

server_actions_common_schema = {
    'status_code': [202]
}

server_actions_delete_password = {
    'status_code': [204]
}

get_console_output = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'output': {'type': 'string'}
        },
        'required': ['output']
    }
}

common_instance_actions = {
    'type': 'object',
    'properties': {
        'action': {'type': 'string'},
        'request_id': {'type': 'string'},
        'user_id': {'type': 'string'},
        'project_id': {'type': 'string'},
        'start_time': {'type': 'string'},
        'message': {'type': ['string', 'null']}
    },
    'required': ['action', 'request_id', 'user_id', 'project_id',
                 'start_time', 'message']
}

instance_action_events = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'event': {'type': 'string'},
            'start_time': {'type': 'string'},
            'finish_time': {'type': 'string'},
            'result': {'type': 'string'},
            'traceback': {'type': ['string', 'null']}
        },
        'required': ['event', 'start_time', 'finish_time', 'result',
                     'traceback']
    }
}

common_get_instance_action = copy.deepcopy(common_instance_actions)

common_get_instance_action['properties'].update({
    'events': instance_action_events})
# 'events' does not come in response body always so it is not
# defined as 'required'

base_list_servers_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'servers': {
                'type': 'array',
                'items': common_show_server
            }
        },
        'required': ['servers']
    }
}
