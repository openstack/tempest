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

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

create_server = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'server': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'security_groups': {'type': 'array'},
                    'links': parameter_types.links,
                    'OS-DCF:diskConfig': {'type': 'string'}
                },
                'additionalProperties': False,
                # NOTE: OS-DCF:diskConfig & security_groups are API extension,
                # and some environments return a response without these
                # attributes.So they are not 'required'.
                'required': ['id', 'links']
            }
        },
        'additionalProperties': False,
        'required': ['server']
    }
}

create_server_with_admin_pass = copy.deepcopy(create_server)
create_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'adminPass': {'type': 'string'}})
create_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('adminPass')

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
                    'additionalProperties': False,
                    'required': ['id', 'links', 'name']
                }
            },
            'servers_links': parameter_types.links
        },
        'additionalProperties': False,
        # NOTE(gmann): servers_links attribute is not necessary to be
        # present always So it is not 'required'.
        'required': ['servers']
    }
}

delete_server = {
    'status_code': [204],
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
                'additionalProperties': False,
                'required': ['id', 'links']},
            {'type': ['string', 'null']}
        ]},
        'flavor': {
            'type': 'object',
            'properties': {
                'id': {'type': 'string'},
                'links': parameter_types.links
            },
            'additionalProperties': False,
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
            'additionalProperties': False,
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
        'hostId': {'type': 'string'},
        'OS-DCF:diskConfig': {'type': 'string'},
        'accessIPv4': parameter_types.access_ip_v4,
        'accessIPv6': parameter_types.access_ip_v6
    },
    'additionalProperties': False,
    # NOTE(GMann): 'progress' attribute is present in the response
    # only when server's status is one of the progress statuses
    # ("ACTIVE","BUILD", "REBUILD", "RESIZE","VERIFY_RESIZE")
    # 'fault' attribute is present in the response
    # only when server's status is one of the  "ERROR", "DELETED".
    # OS-DCF:diskConfig and accessIPv4/v6 are API
    # extensions, and some environments return a response
    # without these attributes.So these are not defined as 'required'.
    'required': ['id', 'name', 'status', 'image', 'flavor',
                 'user_id', 'tenant_id', 'created', 'updated',
                 'metadata', 'links', 'addresses', 'hostId']
}

update_server = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server': common_show_server
        },
        'additionalProperties': False,
        'required': ['server']
    }
}

server_detail = copy.deepcopy(common_show_server)
server_detail['properties'].update({
    'key_name': {'type': ['string', 'null']},
    'security_groups': {'type': 'array'},

    # NOTE: Non-admin users also can see "OS-SRV-USG" and "OS-EXT-AZ"
    # attributes.
    'OS-SRV-USG:launched_at': {'type': ['string', 'null']},
    'OS-SRV-USG:terminated_at': {'type': ['string', 'null']},
    'OS-EXT-AZ:availability_zone': {'type': 'string'},

    # NOTE: Admin users only can see "OS-EXT-STS" and "OS-EXT-SRV-ATTR"
    # attributes.
    'OS-EXT-STS:task_state': {'type': ['string', 'null']},
    'OS-EXT-STS:vm_state': {'type': 'string'},
    'OS-EXT-STS:power_state': {'type': 'integer'},
    'OS-EXT-SRV-ATTR:host': {'type': ['string', 'null']},
    'OS-EXT-SRV-ATTR:instance_name': {'type': 'string'},
    'OS-EXT-SRV-ATTR:hypervisor_hostname': {'type': ['string', 'null']},
    'os-extended-volumes:volumes_attached': {'type': 'array'},
    'config_drive': {'type': 'string'}
})
server_detail['properties']['addresses']['patternProperties'][
    '^[a-zA-Z0-9-_.]+$']['items']['properties'].update({
        'OS-EXT-IPS:type': {'type': 'string'},
        'OS-EXT-IPS-MAC:mac_addr': parameter_types.mac_address})
# NOTE(gmann): Update OS-EXT-IPS:type and OS-EXT-IPS-MAC:mac_addr
# attributes in server address. Those are API extension,
# and some environments return a response without
# these attributes. So they are not 'required'.

get_server = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server': server_detail
        },
        'additionalProperties': False,
        'required': ['server']
    }
}

list_servers_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'servers': {
                'type': 'array',
                'items': server_detail
            },
            'servers_links': parameter_types.links
        },
        'additionalProperties': False,
        # NOTE(gmann): servers_links attribute is not necessary to be
        # present always So it is not 'required'.
        'required': ['servers']
    }
}

rebuild_server = copy.deepcopy(update_server)
rebuild_server['status_code'] = [202]

rebuild_server_with_admin_pass = copy.deepcopy(rebuild_server)
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'adminPass': {'type': 'string'}})
rebuild_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('adminPass')

rescue_server = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'adminPass': {'type': 'string'}
        },
        'additionalProperties': False,
        'required': ['adminPass']
    }
}

list_virtual_interfaces = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'virtual_interfaces': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string'},
                        'mac_address': parameter_types.mac_address,
                        'OS-EXT-VIF-NET:net_id': {'type': 'string'}
                    },
                    'additionalProperties': False,
                    # 'OS-EXT-VIF-NET:net_id' is API extension So it is
                    # not defined as 'required'
                    'required': ['id', 'mac_address']
                }
            }
        },
        'additionalProperties': False,
        'required': ['virtual_interfaces']
    }
}

common_attach_volume_info = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'device': {'type': ['string', 'null']},
        'volumeId': {'type': 'string'},
        'serverId': {'type': ['integer', 'string']}
    },
    'additionalProperties': False,
    # 'device' is optional in response.
    'required': ['id', 'volumeId', 'serverId']
}

attach_volume = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volumeAttachment': common_attach_volume_info
        },
        'additionalProperties': False,
        'required': ['volumeAttachment']
    }
}

detach_volume = {
    'status_code': [202]
}

show_volume_attachment = copy.deepcopy(attach_volume)
show_volume_attachment['response_body']['properties'][
    'volumeAttachment']['properties'].update({'serverId': {'type': 'string'}})

list_volume_attachments = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volumeAttachments': {
                'type': 'array',
                'items': common_attach_volume_info
            }
        },
        'additionalProperties': False,
        'required': ['volumeAttachments']
    }
}
list_volume_attachments['response_body']['properties'][
    'volumeAttachments']['items']['properties'].update(
    {'serverId': {'type': 'string'}})

list_addresses_by_network = {
    'status_code': [200],
    'response_body': parameter_types.addresses
}

list_addresses = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'addresses': parameter_types.addresses
        },
        'additionalProperties': False,
        'required': ['addresses']
    }
}

common_server_group = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'name': {'type': 'string'},
        'policies': {
            'type': 'array',
            'items': {'type': 'string'}
        },
        # 'members' attribute contains the array of instance's UUID of
        # instances present in server group
        'members': {
            'type': 'array',
            'items': {'type': 'string'}
        },
        'metadata': {'type': 'object'}
    },
    'additionalProperties': False,
    'required': ['id', 'name', 'policies', 'members', 'metadata']
}

create_show_server_group = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server_group': common_server_group
        },
        'additionalProperties': False,
        'required': ['server_group']
    }
}

delete_server_group = {
    'status_code': [204]
}

list_server_groups = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server_groups': {
                'type': 'array',
                'items': common_server_group
            }
        },
        'additionalProperties': False,
        'required': ['server_groups']
    }
}

instance_actions = {
    'type': 'object',
    'properties': {
        'action': {'type': 'string'},
        'request_id': {'type': 'string'},
        'user_id': {'type': 'string'},
        'project_id': {'type': 'string'},
        'start_time': {'type': 'string'},
        'message': {'type': ['string', 'null']},
        'instance_uuid': {'type': 'string'}
    },
    'additionalProperties': False,
    'required': ['action', 'request_id', 'user_id', 'project_id',
                 'start_time', 'message', 'instance_uuid']
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
        'additionalProperties': False,
        'required': ['event', 'start_time', 'finish_time', 'result',
                     'traceback']
    }
}

list_instance_actions = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'instanceActions': {
                'type': 'array',
                'items': instance_actions
            }
        },
        'additionalProperties': False,
        'required': ['instanceActions']
    }
}

instance_actions_with_events = copy.deepcopy(instance_actions)
instance_actions_with_events['properties'].update({
    'events': instance_action_events})
# 'events' does not come in response body always so it is not
# defined as 'required'

show_instance_action = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'instanceAction': instance_actions_with_events
        },
        'additionalProperties': False,
        'required': ['instanceAction']
    }
}

show_password = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'password': {'type': 'string'}
        },
        'additionalProperties': False,
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
                'additionalProperties': False,
                'required': ['type', 'url']
            }
        },
        'additionalProperties': False,
        'required': ['console']
    }
}

get_console_output = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'output': {'type': 'string'}
        },
        'additionalProperties': False,
        'required': ['output']
    }
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
        'additionalProperties': False,
        'required': ['metadata']
    }
}

list_server_metadata = copy.deepcopy(set_server_metadata)

update_server_metadata = copy.deepcopy(set_server_metadata)

delete_server_metadata_item = {
    'status_code': [204]
}

set_show_server_metadata_item = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'meta': {
                'type': 'object',
                'patternProperties': {
                    '^.+$': {'type': 'string'}
                }
            }
        },
        'additionalProperties': False,
        'required': ['meta']
    }
}

server_actions_common_schema = {
    'status_code': [202]
}

server_actions_delete_password = {
    'status_code': [204]
}

server_actions_confirm_resize = copy.deepcopy(
    server_actions_delete_password)

update_attached_volume = {
    'status_code': [202]
}
