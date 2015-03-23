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

common_floating_ip_info = {
    'type': 'object',
    'properties': {
        # NOTE: Now the type of 'id' is integer, but
        # here allows 'string' also because we will be
        # able to change it to 'uuid' in the future.
        'id': {'type': ['integer', 'string']},
        'pool': {'type': ['string', 'null']},
        'instance_id': {'type': ['string', 'null']},
        'ip': {
            'type': 'string',
            'format': 'ip-address'
        },
        'fixed_ip': {
            'type': ['string', 'null'],
            'format': 'ip-address'
        }
    },
    'required': ['id', 'pool', 'instance_id',
                 'ip', 'fixed_ip'],

}
list_floating_ips = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'floating_ips': {
                'type': 'array',
                'items': common_floating_ip_info
            },
        },
        'required': ['floating_ips'],
    }
}

floating_ip = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'floating_ip': common_floating_ip_info
        },
        'required': ['floating_ip'],
    }
}

floating_ip_pools = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'floating_ip_pools': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'}
                    },
                    'required': ['name'],
                }
            }
        },
        'required': ['floating_ip_pools'],
    }
}

add_remove_floating_ip = {
    'status_code': [202]
}

create_floating_ips_bulk = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'floating_ips_bulk_create': {
                'type': 'object',
                'properties': {
                    'interface': {'type': ['string', 'null']},
                    'ip_range': {'type': 'string'},
                    'pool': {'type': ['string', 'null']},
                },
                'required': ['interface', 'ip_range', 'pool'],
            }
        },
        'required': ['floating_ips_bulk_create'],
    }
}

delete_floating_ips_bulk = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'floating_ips_bulk_delete': {'type': 'string'}
        },
        'required': ['floating_ips_bulk_delete'],
    }
}

list_floating_ips_bulk = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'floating_ip_info': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'address': {
                            'type': 'string',
                            'format': 'ip-address'
                        },
                        'instance_uuid': {'type': ['string', 'null']},
                        'interface': {'type': ['string', 'null']},
                        'pool': {'type': ['string', 'null']},
                        'project_id': {'type': ['string', 'null']},
                        'fixed_ip': {
                            'type': ['string', 'null'],
                            'format': 'ip-address'
                        }
                    },
                    # NOTE: fixed_ip is introduced after JUNO release,
                    # So it is not defined as 'required'.
                    'required': ['address', 'instance_uuid', 'interface',
                                 'pool', 'project_id'],
                }
            }
        },
        'required': ['floating_ip_info'],
    }
}
