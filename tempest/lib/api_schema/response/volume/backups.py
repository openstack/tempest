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

import copy

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

common_show_backup = {
    'type': 'object',
    'properties': {
        'status': {'type': 'string'},
        'object_count': {'type': 'integer'},
        'container': {'type': ['string', 'null']},
        'description': {'type': ['string', 'null']},
        'links': parameter_types.links,
        'availability_zone': {'type': ['string', 'null']},
        'created_at': parameter_types.date_time,
        'updated_at': parameter_types.date_time_or_null,
        'name': {'type': ['string', 'null']},
        'has_dependent_backups': {'type': 'boolean'},
        'volume_id': {'type': 'string', 'format': 'uuid'},
        'fail_reason': {'type': ['string', 'null']},
        'size': {'type': 'integer'},
        'id': {'type': 'string', 'format': 'uuid'},
        'is_incremental': {'type': 'boolean'},
        'data_timestamp': parameter_types.date_time_or_null,
        'snapshot_id': {'type': ['string', 'null']},
        # TODO(zhufl): os-backup-project-attr:project_id is added
        # in 3.18, we should move it to the 3.18 schema file when
        # microversion is supported in volume interfaces.
        'os-backup-project-attr:project_id': {
            'type': 'string', 'format': 'uuid'},
        # TODO(zhufl): metadata is added in 3.43, we should move it
        # to the 3.43 schema file when microversion is supported
        # in volume interfaces.
        'metadata': {'^.+$': {'type': 'string'}},
        # TODO(zhufl): user_id is added in 3.56, we should move it
        # to the 3.56 schema file when microversion is supported
        # in volume interfaces.
        'user_id': {'type': 'string'},
    },
    'additionalProperties': False,
    'required': ['status', 'object_count', 'fail_reason', 'links',
                 'created_at', 'updated_at', 'name', 'volume_id', 'size', 'id',
                 'data_timestamp']
}

create_backup = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'backup': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'links': parameter_types.links,
                    'name': {'type': ['string', 'null']},
                    # TODO(zhufl): metadata is added in 3.43, we should move it
                    # to the 3.43 schema file when microversion is supported
                    # in volume interfaces.
                    'metadata': {'^.+$': {'type': 'string'}},
                },
                'additionalProperties': False,
                'required': ['id', 'links', 'name']
            }
        },
        'additionalProperties': False,
        'required': ['backup']
    }
}

update_backup = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'backup': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'links': parameter_types.links,
                    'name': {'type': ['string', 'null']},
                    'metadata': {'^.+$': {'type': 'string'}}
                },
                'additionalProperties': False,
                'required': ['id', 'links', 'name']
            }
        },
        'additionalProperties': False,
        'required': ['backup']
    }
}

restore_backup = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'restore': {
                'type': 'object',
                'properties': {
                    'backup_id': {'type': 'string', 'format': 'uuid'},
                    'volume_id': {'type': 'string', 'format': 'uuid'},
                    'volume_name': {'type': 'string'},
                },
                'additionalProperties': False,
                'required': ['backup_id', 'volume_id', 'volume_name']
            }
        },
        'additionalProperties': False,
        'required': ['restore']
    }
}

delete_backup = {'status_code': [202]}

show_backup = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'backup': common_show_backup
        },
        'additionalProperties': False,
        'required': ['backup']
    }
}

list_backups_no_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'backups': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'links': parameter_types.links,
                        'id': {'type': 'string', 'format': 'uuid'},
                        'name': {'type': ['string', 'null']},
                        # TODO(zhufl): count is added in 3.45, we should move
                        # it to the 3.45 schema file when microversion is
                        # supported in volume interfaces
                        'count': {'type': 'integer'}
                    },
                    'additionalProperties': False,
                    'required': ['links', 'id', 'name']
                }
            }
        },
        'additionalProperties': False,
        'required': ['backups'],
    }
}

list_backups_detail = copy.deepcopy(common_show_backup)
# TODO(zhufl): count is added in 3.45, we should move it to the 3.45 schema
# file when microversion is supported in volume interfaces
list_backups_detail['properties'].update({'count': {'type': 'integer'}})
list_backups_with_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'backups': {
                'type': 'array',
                'items': list_backups_detail
            }
        },
        'additionalProperties': False,
        'required': ['backups'],
    }
}

export_backup = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'backup-record': {
                'type': 'object',
                'properties': {
                    'backup_service': {'type': 'string'},
                    'backup_url': {'type': 'string'}
                },
                'additionalProperties': False,
                'required': ['backup_service', 'backup_url']
            }
        },
        'additionalProperties': False,
        'required': ['backup-record']
    }
}

import_backup = {
    'status_code': [201],
    'response_body': {
        'type': 'object',
        'properties': {
            'backup': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string', 'format': 'uuid'},
                    'links': parameter_types.links,
                    'name': {'type': ['string', 'null']},
                },
                'additionalProperties': False,
                'required': ['id', 'links', 'name']
            }
        },
        'additionalProperties': False,
        'required': ['backup']
    }
}

reset_backup_status = {'status_code': [202]}
