# Copyright 2017 Mirantis Inc.
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
from tempest.lib.api_schema.response.compute.v2_47 import servers as servers247


show_server_diagnostics = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'state': {
                'type': 'string', 'enum': [
                    'pending', 'running', 'paused', 'shutdown', 'crashed',
                    'suspended']
            },
            'driver': {
                'type': 'string', 'enum': [
                    'libvirt', 'xenapi', 'vmwareapi', 'ironic', 'hyperv']
            },
            'hypervisor': {'type': ['string', 'null']},
            'hypervisor_os': {'type': ['string', 'null']},
            'uptime': {'type': ['integer', 'null']},
            'config_drive': {'type': 'boolean'},
            'num_cpus': {'type': 'integer'},
            'num_nics': {'type': 'integer'},
            'num_disks': {'type': 'integer'},
            'memory_details': {
                'type': 'object',
                'properties': {
                    'maximum': {'type': ['integer', 'null']},
                    'used': {'type': ['integer', 'null']}
                },
                'additionalProperties': False,
                'required': ['maximum', 'used']
            },
            'cpu_details': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': ['integer', 'null']},
                        'time': {'type': ['integer', 'null']},
                        'utilisation': {'type': ['integer', 'null']}
                    },
                    'additionalProperties': False,
                    'required': ['id', 'time', 'utilisation']
                }
            },
            'nic_details': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'mac_address': {'oneOf': [parameter_types.mac_address,
                                                  {'type': 'null'}]},
                        'rx_octets': {'type': ['integer', 'null']},
                        'rx_errors': {'type': ['integer', 'null']},
                        'rx_drop': {'type': ['integer', 'null']},
                        'rx_packets': {'type': ['integer', 'null']},
                        'rx_rate': {'type': ['integer', 'null']},
                        'tx_octets': {'type': ['integer', 'null']},
                        'tx_errors': {'type': ['integer', 'null']},
                        'tx_drop': {'type': ['integer', 'null']},
                        'tx_packets': {'type': ['integer', 'null']},
                        'tx_rate': {'type': ['integer', 'null']}
                    },
                    'additionalProperties': False,
                    'required': ['mac_address', 'rx_octets', 'rx_errors',
                                 'rx_drop',
                                 'rx_packets', 'rx_rate', 'tx_octets',
                                 'tx_errors',
                                 'tx_drop', 'tx_packets', 'tx_rate']
                }
            },
            'disk_details': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'read_bytes': {'type': ['integer', 'null']},
                        'read_requests': {'type': ['integer', 'null']},
                        'write_bytes': {'type': ['integer', 'null']},
                        'write_requests': {'type': ['integer', 'null']},
                        'errors_count': {'type': ['integer', 'null']}
                    },
                    'additionalProperties': False,
                    'required': ['read_bytes', 'read_requests', 'write_bytes',
                                 'write_requests', 'errors_count']
                }
            }
        },
        'additionalProperties': False,
        'required': [
            'state', 'driver', 'hypervisor', 'hypervisor_os', 'uptime',
            'config_drive', 'num_cpus', 'num_nics', 'num_disks',
            'memory_details', 'cpu_details', 'nic_details', 'disk_details'],
    }
}

get_server = copy.deepcopy(servers247.get_server)
