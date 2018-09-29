# Copyright 2015 NEC Corporation.  All rights reserved.
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

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

create_group = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'group': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                },
                'additionalProperties': False,
                'required': ['id', 'name']
            }
        },
        'additionalProperties': False,
        'required': ['group']
    }
}

delete_group = {'status_code': [202]}

show_group = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'group': {
                'type': 'object',
                'properties': {
                    'status': {'type': 'string'},
                    'description': {'type': ['string', 'null']},
                    'availability_zone': {'type': 'string'},
                    'created_at': parameter_types.date_time,
                    'group_type': {'type': 'string', 'format': 'uuid'},
                    'group_snapshot_id': {'type': ['string', 'null']},
                    'source_group_id': {'type': ['string', 'null']},
                    'volume_types': {
                        'type': 'array',
                        'items': {'type': 'string', 'format': 'uuid'}
                    },
                    'id': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                    # TODO(zhufl): volumes is added in 3.25, we should move it
                    # to the 3.25 schema file when microversion is supported
                    # in volume interfaces
                    'volumes': {
                        'type': 'array',
                        'items': {'type': 'string', 'format': 'uuid'}
                    },
                    'replication_status': {'type': 'string'}
                },
                'additionalProperties': False,
                'required': ['status', 'description', 'created_at',
                             'group_type', 'volume_types', 'id', 'name']
            }
        },
        'additionalProperties': False,
        'required': ['group']
    }
}

list_groups_no_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'groups': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'id': {'type': 'string', 'format': 'uuid'},
                        'name': {'type': 'string'}
                    },
                    'additionalProperties': False,
                    'required': ['id', 'name'],
                }
            }
        },
        'additionalProperties': False,
        'required': ['groups'],
    }
}

list_groups_with_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'groups': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'status': {'type': 'string'},
                        'description': {'type': ['string', 'null']},
                        'availability_zone': {'type': 'string'},
                        'created_at': parameter_types.date_time,
                        'group_type': {'type': 'string', 'format': 'uuid'},
                        'group_snapshot_id': {'type': ['string', 'null']},
                        'source_group_id': {'type': ['string', 'null']},
                        'volume_types': {
                            'type': 'array',
                            'items': {'type': 'string', 'format': 'uuid'}
                        },
                        'id': {'type': 'string', 'format': 'uuid'},
                        'name': {'type': 'string'},
                        # TODO(zhufl): volumes is added in 3.25, we should
                        # move it to the 3.25 schema file when microversion
                        # is supported in volume interfaces
                        'volumes': {
                            'type': 'array',
                            'items': {'type': 'string', 'format': 'uuid'}
                        },
                    },
                    'additionalProperties': False,
                    'required': ['status', 'description', 'created_at',
                                 'group_type', 'volume_types', 'id', 'name']
                }
            }
        },
        'additionalProperties': False,
        'required': ['groups'],
    }
}

create_group_from_source = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'group': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'name': {'type': 'string'},
                },
                'additionalProperties': False,
                'required': ['id', 'name']
            }
        },
        'additionalProperties': False,
        'required': ['group']
    }
}
update_group = {'status_code': [202]}
reset_group_status = {'status_code': [202]}
