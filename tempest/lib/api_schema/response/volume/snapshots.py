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
import copy

from tempest.lib.api_schema.response.compute.v2_1 import parameter_types

metadata = {
    'type': 'object',
    'patternProperties': {
        '^.+$': {'type': 'string'}
    }
}

common_snapshot_schema = {
    'type': 'object',
    'properties': {
        'status': {'type': 'string'},
        'description': {'type': ['string', 'null']},
        'created_at': parameter_types.date_time,
        'name': {'type': ['string', 'null']},
        'volume_id': {'type': 'string', 'format': 'uuid'},
        'metadata': metadata,
        'id': {'type': 'string', 'format': 'uuid'},
        'size': {'type': 'integer'},
        'updated_at': parameter_types.date_time_or_null,
        # TODO(zhufl): user_id is added in 3.41, we should move it
        # to the 3.41 schema file when microversion is supported
        # in volume interfaces
        # 'user_id': {'type': 'string', 'format': 'uuid'}
    },
    'additionalProperties': False,
    'required': ['status', 'description', 'created_at', 'metadata',
                 'name', 'volume_id', 'id', 'size', 'updated_at']
}

common_snapshot_detail_schema = copy.deepcopy(common_snapshot_schema)
common_snapshot_detail_schema['properties'].update(
    {'os-extended-snapshot-attributes:progress': {'type': 'string'},
     'os-extended-snapshot-attributes:project_id': {
         'type': 'string', 'format': 'uuid'}})
common_snapshot_detail_schema['required'].extend(
    ['os-extended-snapshot-attributes:progress',
     'os-extended-snapshot-attributes:project_id'])

list_snapshots_no_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'snapshots': {
                'type': 'array',
                'items': common_snapshot_schema
            },
            'snapshots_links': parameter_types.links,
            # TODO(zhufl): count is added in 3.45, we should move
            # it to the 3.45 schema file when microversion is
            # supported in volume interfaces
            # 'count': {'type': 'integer'}
        },
        'additionalProperties': False,
        'required': ['snapshots'],
    }
}

list_snapshots_with_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'snapshots': {
                'type': 'array',
                'items': common_snapshot_detail_schema
            },
            'snapshots_links': parameter_types.links,
            # TODO(zhufl): count is added in 3.45, we should move
            # it to the 3.45 schema file when microversion is
            # supported in volume interfaces
            # 'count': {'type': 'integer'},
        },
        'additionalProperties': False,
        'required': ['snapshots'],
    }
}

show_snapshot = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'snapshot': common_snapshot_detail_schema
        },
        'additionalProperties': False,
        'required': ['snapshot'],
    }
}

create_snapshot = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'snapshot': common_snapshot_schema
        },
        'additionalProperties': False,
        'required': ['snapshot'],
    }
}

update_snapshot = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'snapshot': common_snapshot_schema
        },
        'additionalProperties': False,
        'required': ['snapshot'],
    }
}

delete_snapshot = {'status_code': [202]}
reset_snapshot_status = {'status_code': [202]}
update_snapshot_status = {'status_code': [202]}

create_snapshot_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'metadata': metadata
        },
        'additionalProperties': False,
        'required': ['metadata'],
    }
}

show_snapshot_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'metadata': metadata
        },
        'additionalProperties': False,
        'required': ['metadata'],
    }
}

update_snapshot_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'metadata': metadata
        },
        'additionalProperties': False,
        'required': ['metadata'],
    }
}

show_snapshot_metadata_item = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'meta': metadata
        },
        'additionalProperties': False,
        'required': ['meta'],
    }
}

update_snapshot_metadata_item = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'meta': metadata
        },
        'additionalProperties': False,
        'required': ['meta'],
    }
}

delete_snapshot_metadata_item = {'status_code': [200]}
force_delete_snapshot = {'status_code': [202]}
unmanage_snapshot = {'status_code': [202]}
