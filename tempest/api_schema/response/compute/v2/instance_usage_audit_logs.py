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

common_instance_usage_audit_log = {
    'type': 'object',
    'properties': {
        'hosts_not_run': {
            'type': 'array',
            'items': {'type': 'string'}
        },
        'log': {'type': 'object'},
        'num_hosts': {'type': 'integer'},
        'num_hosts_done': {'type': 'integer'},
        'num_hosts_not_run': {'type': 'integer'},
        'num_hosts_running': {'type': 'integer'},
        'overall_status': {'type': 'string'},
        'period_beginning': {'type': 'string'},
        'period_ending': {'type': 'string'},
        'total_errors': {'type': 'integer'},
        'total_instances': {'type': 'integer'}
    },
    'required': ['hosts_not_run', 'log', 'num_hosts', 'num_hosts_done',
                 'num_hosts_not_run', 'num_hosts_running', 'overall_status',
                 'period_beginning', 'period_ending', 'total_errors',
                 'total_instances']
}

get_instance_usage_audit_log = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'instance_usage_audit_log': common_instance_usage_audit_log
        },
        'required': ['instance_usage_audit_log']
    }
}

list_instance_usage_audit_log = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'instance_usage_audit_logs': common_instance_usage_audit_log
        },
        'required': ['instance_usage_audit_logs']
    }
}
