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

from tempest.api_schema.compute import parameter_types
from tempest.api_schema.compute import servers

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
                    'adminPass': {'type': 'string'},
                    'OS-DCF:diskConfig': {'type': 'string'}
                },
                # NOTE: OS-DCF:diskConfig is API extension, and some
                # environments return a response without the attribute.
                # So it is not 'required'.
                # NOTE: adminPass is not required because it can be deactivated
                # with nova API flag enable_instance_password=False
                'required': ['id', 'security_groups', 'links']
            }
        },
        'required': ['server']
    }
}

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

attach_volume = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volumeAttachment': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'device': {'type': 'string'},
                    'volumeId': {'type': 'string'},
                    'serverId': {'type': ['integer', 'string']}
                },
                'required': ['id', 'device', 'volumeId', 'serverId']
            }
        },
        'required': ['volumeAttachment']
    }
}

detach_volume = {
    'status_code': [202]
}

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

list_servers_detail = copy.deepcopy(servers.base_list_servers_detail)
list_servers_detail['response_body']['properties']['servers']['items'][
    'properties'].update({
        'hostId': {'type': 'string'},
        'OS-DCF:diskConfig': {'type': 'string'},
        'accessIPv4': parameter_types.access_ip_v4,
        'accessIPv6': parameter_types.access_ip_v6
    })
# NOTE(GMann): OS-DCF:diskConfig and accessIPv4/v6 are API
# extensions, and some environments return a response
# without these attributes. So they are not 'required'.
list_servers_detail['response_body']['properties']['servers']['items'][
    'required'].append('hostId')
