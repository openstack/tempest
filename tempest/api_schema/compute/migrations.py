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

list_migrations = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'migrations': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'integer'},
                        'status': {'type': 'string'},
                        'instance_uuid': {'type': 'string'},
                        'source_node': {'type': 'string'},
                        'source_compute': {'type': 'string'},
                        'dest_node': {'type': 'string'},
                        'dest_compute': {'type': 'string'},
                        'dest_host': {'type': 'string'},
                        'old_instance_type_id': {'type': 'integer'},
                        'new_instance_type_id': {'type': 'integer'},
                        'created_at': {'type': 'string'},
                        'updated_at': {'type': ['string', 'null']}
                    },
                    'required': [
                        'id', 'status', 'instance_uuid', 'source_node',
                        'source_compute', 'dest_node', 'dest_compute',
                        'dest_host', 'old_instance_type_id',
                        'new_instance_type_id', 'created_at', 'updated_at'
                    ]
                }
            }
        },
        'required': ['migrations']
    }
}
