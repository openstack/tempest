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
from tempest.api_schema.response.compute import servers

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
                # NOTE: OS-DCF:diskConfig & security_groups are API extension,
                # and some environments return a response without these
                # attributes.So they are not 'required'.
                'required': ['id', 'links']
            }
        },
        'required': ['server']
    }
}

create_server_with_admin_pass = copy.deepcopy(create_server)
create_server_with_admin_pass['response_body']['properties']['server'][
    'properties'].update({'adminPass': {'type': 'string'}})
create_server_with_admin_pass['response_body']['properties']['server'][
    'required'].append('adminPass')

update_server = copy.deepcopy(servers.base_update_get_server)
update_server['response_body']['properties']['server']['properties'].update({
    'hostId': {'type': 'string'},
    'OS-DCF:diskConfig': {'type': 'string'},
    'accessIPv4': parameter_types.access_ip_v4,
    'accessIPv6': parameter_types.access_ip_v6
})
update_server['response_body']['properties']['server']['required'].append(
    # NOTE: OS-DCF:diskConfig and accessIPv4/v6 are API
    # extensions, and some environments return a response
    # without these attributes. So they are not 'required'.
    'hostId'
)

get_server = copy.deepcopy(servers.base_update_get_server)
get_server['response_body']['properties']['server']['properties'].update({
    'key_name': {'type': ['string', 'null']},
    'hostId': {'type': 'string'},
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
    'OS-DCF:diskConfig': {'type': 'string'},
    'accessIPv4': parameter_types.access_ip_v4,
    'accessIPv6': parameter_types.access_ip_v6,
    'config_drive': {'type': 'string'}
})
get_server['response_body']['properties']['server']['required'].append(
    # NOTE: OS-SRV-USG, OS-EXT-AZ, OS-EXT-STS, OS-EXT-SRV-ATTR,
    # os-extended-volumes, OS-DCF and accessIPv4/v6 are API
    # extension, and some environments return a response without
    # these attributes. So they are not 'required'.
    'hostId'
)
# NOTE(gmann): Update OS-EXT-IPS:type and OS-EXT-IPS-MAC:mac_addr
# attributes in server address. Those are API extension,
# and some environments return a response without
# these attributes. So they are not 'required'.
get_server['response_body']['properties']['server']['properties'][
    'addresses']['patternProperties']['^[a-zA-Z0-9-_.]+$']['items'][
    'properties'].update({
        'OS-EXT-IPS:type': {'type': 'string'},
        'OS-EXT-IPS-MAC:mac_addr': parameter_types.mac_address})

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
                    # 'OS-EXT-VIF-NET:net_id' is API extension So it is
                    # not defined as 'required'
                    'required': ['id', 'mac_address']
                }
            }
        },
        'required': ['virtual_interfaces']
    }
}

common_attach_volume_info = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'device': {'type': 'string'},
        'volumeId': {'type': 'string'},
        'serverId': {'type': ['integer', 'string']}
    },
    'required': ['id', 'device', 'volumeId', 'serverId']
}

attach_volume = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volumeAttachment': common_attach_volume_info
        },
        'required': ['volumeAttachment']
    }
}

detach_volume = {
    'status_code': [202]
}

get_volume_attachment = copy.deepcopy(attach_volume)
get_volume_attachment['response_body']['properties'][
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
        'required': ['volumeAttachments']
    }
}
list_volume_attachments['response_body']['properties'][
    'volumeAttachments']['items']['properties'].update(
    {'serverId': {'type': 'string'}})

set_get_server_metadata_item = {
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
        'required': ['meta']
    }
}

list_addresses_by_network = {
    'status_code': [200],
    'response_body': parameter_types.addresses
}

server_actions_confirm_resize = copy.deepcopy(
    servers.server_actions_delete_password)

list_addresses = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'addresses': parameter_types.addresses
        },
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
    'required': ['id', 'name', 'policies', 'members', 'metadata']
}

create_get_server_group = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'server_group': common_server_group
        },
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
        'required': ['server_groups']
    }
}

instance_actions_object = copy.deepcopy(servers.common_instance_actions)
instance_actions_object[
    'properties'].update({'instance_uuid': {'type': 'string'}})
instance_actions_object['required'].extend(['instance_uuid'])

list_instance_actions = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'instanceActions': {
                'type': 'array',
                'items': instance_actions_object
            }
        },
        'required': ['instanceActions']
    }
}

get_instance_actions_object = copy.deepcopy(servers.common_get_instance_action)
get_instance_actions_object[
    'properties'].update({'instance_uuid': {'type': 'string'}})
get_instance_actions_object['required'].extend(['instance_uuid'])

get_instance_action = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'instanceAction': get_instance_actions_object
        },
        'required': ['instanceAction']
    }
}

list_servers_detail = copy.deepcopy(servers.base_list_servers_detail)
list_servers_detail['response_body']['properties']['servers']['items'][
    'properties'].update({
        'key_name': {'type': ['string', 'null']},
        'hostId': {'type': 'string'},
        'OS-DCF:diskConfig': {'type': 'string'},
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
        'accessIPv4': parameter_types.access_ip_v4,
        'accessIPv6': parameter_types.access_ip_v6,
        'config_drive': {'type': 'string'}
    })
# NOTE(GMann): OS-SRV-USG, OS-EXT-AZ, OS-EXT-STS, OS-EXT-SRV-ATTR,
# os-extended-volumes, OS-DCF and accessIPv4/v6 are API
# extensions, and some environments return a response without
# these attributes. So they are not 'required'.
list_servers_detail['response_body']['properties']['servers']['items'][
    'required'].append('hostId')
# NOTE(gmann): Update OS-EXT-IPS:type and OS-EXT-IPS-MAC:mac_addr
# attributes in server address. Those are API extension,
# and some environments return a response without
# these attributes. So they are not 'required'.
list_servers_detail['response_body']['properties']['servers']['items'][
    'properties']['addresses']['patternProperties']['^[a-zA-Z0-9-_.]+$'][
    'items']['properties'].update({
        'OS-EXT-IPS:type': {'type': 'string'},
        'OS-EXT-IPS-MAC:mac_addr': parameter_types.mac_address})
# Defining 'servers_links' attributes for V2 server schema
list_servers_detail['response_body'][
    'properties'].update({'servers_links': parameter_types.links})
# NOTE(gmann): servers_links attribute is not necessary to be
# present always So it is not 'required'.

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
        'required': ['adminPass']
    }
}
