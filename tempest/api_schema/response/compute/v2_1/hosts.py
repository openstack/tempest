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


list_hosts = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'hosts': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'host_name': {'type': 'string'},
                        'service': {'type': 'string'},
                        'zone': {'type': 'string'}
                    },
                    'required': ['host_name', 'service', 'zone']
                }
            }
        },
        'required': ['hosts']
    }
}

get_host_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'host': {
                'type': 'array',
                'item': {
                    'type': 'object',
                    'properties': {
                        'resource': {
                            'type': 'object',
                            'properties': {
                                'cpu': {'type': 'integer'},
                                'disk_gb': {'type': 'integer'},
                                'host': {'type': 'string'},
                                'memory_mb': {'type': 'integer'},
                                'project': {'type': 'string'}
                            },
                            'required': ['cpu', 'disk_gb', 'host',
                                         'memory_mb', 'project']
                        }
                    },
                    'required': ['resource']
                }
            }
        },
        'required': ['host']
    }
}

startup_host = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'host': {'type': 'string'},
            'power_action': {'enum': ['startup']}
        },
        'required': ['host', 'power_action']
    }
}

# The 'power_action' attribute of 'shutdown_host' API is 'shutdown'
shutdown_host = copy.deepcopy(startup_host)

shutdown_host['response_body']['properties']['power_action'] = {
    'enum': ['shutdown']
}

# The 'power_action' attribute of 'reboot_host' API is 'reboot'
reboot_host = copy.deepcopy(startup_host)

reboot_host['response_body']['properties']['power_action'] = {
    'enum': ['reboot']
}

update_host = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'host': {'type': 'string'},
            'maintenance_mode': {'enum': ['on_maintenance',
                                          'off_maintenance']},
            'status': {'enum': ['enabled', 'disabled']}
        },
        'required': ['host', 'maintenance_mode', 'status']
    }
}
