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

_server_usages = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'ended_at': {
                'oneOf': [
                    {'type': 'string'},
                    {'type': 'null'}
                ]
            },
            'flavor': {'type': 'string'},
            'hours': {'type': 'number'},
            'instance_id': {'type': 'string'},
            'local_gb': {'type': 'integer'},
            'memory_mb': {'type': 'integer'},
            'name': {'type': 'string'},
            'started_at': {'type': 'string'},
            'state': {'type': 'string'},
            'tenant_id': {'type': 'string'},
            'uptime': {'type': 'integer'},
            'vcpus': {'type': 'integer'},
        },
        'required': ['ended_at', 'flavor', 'hours', 'instance_id', 'local_gb',
                     'memory_mb', 'name', 'started_at', 'state', 'tenant_id',
                     'uptime', 'vcpus']
    }
}

_tenant_usage_list = {
    'type': 'object',
    'properties': {
        'server_usages': _server_usages,
        'start': {'type': 'string'},
        'stop': {'type': 'string'},
        'tenant_id': {'type': 'string'},
        'total_hours': {'type': 'number'},
        'total_local_gb_usage': {'type': 'number'},
        'total_memory_mb_usage': {'type': 'number'},
        'total_vcpus_usage': {'type': 'number'},
    },
    'required': ['start', 'stop', 'tenant_id',
                 'total_hours', 'total_local_gb_usage',
                 'total_memory_mb_usage', 'total_vcpus_usage']
}

# 'required' of get_tenant is different from list_tenant's.
_tenant_usage_get = copy.deepcopy(_tenant_usage_list)
_tenant_usage_get['required'] = ['server_usages', 'start', 'stop', 'tenant_id',
                                 'total_hours', 'total_local_gb_usage',
                                 'total_memory_mb_usage', 'total_vcpus_usage']

list_tenant = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'tenant_usages': {
                'type': 'array',
                'items': _tenant_usage_list
            }
        },
        'required': ['tenant_usages']
    }
}

get_tenant = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'tenant_usage': _tenant_usage_get
        },
        'required': ['tenant_usage']
    }
}
