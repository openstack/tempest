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

hypervisor_statistics = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'hypervisor_statistics': {
                'type': 'object',
                'properties': {
                    'count': {'type': 'integer'},
                    'current_workload': {'type': 'integer'},
                    'disk_available_least': {'type': 'integer'},
                    'free_disk_gb': {'type': 'integer'},
                    'free_ram_mb': {'type': 'integer'},
                    'local_gb': {'type': 'integer'},
                    'local_gb_used': {'type': 'integer'},
                    'memory_mb': {'type': 'integer'},
                    'memory_mb_used': {'type': 'integer'},
                    'running_vms': {'type': 'integer'},
                    'vcpus': {'type': 'integer'},
                    'vcpus_used': {'type': 'integer'}
                },
                'required': ['count', 'current_workload',
                             'disk_available_least', 'free_disk_gb',
                             'free_ram_mb', 'local_gb', 'local_gb_used',
                             'memory_mb', 'memory_mb_used', 'running_vms',
                             'vcpus', 'vcpus_used']
            }
        },
        'required': ['hypervisor_statistics']
    }
}
