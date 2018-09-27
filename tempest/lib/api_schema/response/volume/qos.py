# Copyright 2018 ZTE Corporation.  All rights reserved.
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

show_qos = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'qos_specs': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'id': {'type': 'string', 'format': 'uuid'},
                    'consumer': {'type': 'string'},
                    'specs': {'type': ['object', 'null']},
                },
                'additionalProperties': False,
                'required': ['name', 'id', 'specs']
            },
            'links': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'href': {'type': 'string',
                                 'format': 'uri'},
                        'rel': {'type': 'string'},
                    },
                    'additionalProperties': False,
                    'required': ['href', 'rel']
                }
            }
        },
        'additionalProperties': False,
        'required': ['qos_specs', 'links']
    }
}

delete_qos = {'status_code': [202]}

list_qos = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'qos_specs': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'specs': {
                            'type': 'object',
                            'patternProperties': {'^.+$': {'type': 'string'}}
                        },
                        'consumer': {'type': 'string'},
                        'id': {'type': 'string', 'format': 'uuid'},
                        'name': {'type': 'string'}
                    },
                    'additionalProperties': False,
                    'required': ['specs', 'id', 'name']
                }
            }
        },
        'additionalProperties': False,
        'required': ['qos_specs']
    }
}

set_qos_key = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'qos_specs': {
                'type': 'object',
                'patternProperties': {'^.+$': {'type': 'string'}}
            },
        },
        'additionalProperties': False,
        'required': ['qos_specs']
    }
}

unset_qos_key = {'status_code': [202]}
associate_qos = {'status_code': [202]}

show_association_qos = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'qos_associations': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'association_type': {'type': 'string'},
                        'id': {'type': 'string', 'format': 'uuid'},
                        'name': {'type': 'string'}
                    },
                    'additionalProperties': False,
                    'required': ['association_type', 'id', 'name']
                }
            },
        },
        'additionalProperties': False,
        'required': ['qos_associations']
    }
}

disassociate_qos = {'status_code': [202]}
disassociate_all_qos = {'status_code': [202]}
