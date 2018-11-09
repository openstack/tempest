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

attachments = {
    'type': 'array',
    'items': {
        'type': 'object',
        'properties': {
            'server_id': {'type': 'string', 'format': 'uuid'},
            'attachment_id': {'type': 'string', 'format': 'uuid'},
            'attached_at': parameter_types.date_time_or_null,
            'host_name': {'type': ['string', 'null']},
            'volume_id': {'type': 'string', 'format': 'uuid'},
            'device': {'type': ['string', 'null']},
            'id': {'type': 'string', 'format': 'uuid'}
        },
        'additionalProperties': False,
        'required': ['server_id', 'attachment_id', 'host_name',
                     'volume_id', 'device', 'id']
    }
}

common_show_volume = {
    'type': 'object',
    'properties': {
        'migration_status': {'type': ['string', 'null']},
        'attachments': attachments,
        'links': parameter_types.links,
        'availability_zone': {'type': ['string', 'null']},
        'os-vol-host-attr:host': {
            'type': ['string', 'null'], 'pattern': '.+@.+#.+'},
        'encrypted': {'type': 'boolean'},
        'updated_at': parameter_types.date_time_or_null,
        'replication_status': {'type': ['string', 'null']},
        'snapshot_id': parameter_types.uuid_or_null,
        'id': {'type': 'string', 'format': 'uuid'},
        'size': {'type': 'integer'},
        'user_id': {'type': 'string', 'format': 'uuid'},
        'os-vol-tenant-attr:tenant_id': {'type': 'string',
                                         'format': 'uuid'},
        'os-vol-mig-status-attr:migstat': {'type': ['string', 'null']},
        'metadata': {'type': 'object'},
        'status': {'type': 'string'},
        'volume_image_metadata': {'type': ['object', 'null']},
        'description': {'type': ['string', 'null']},
        'multiattach': {'type': 'boolean'},
        'source_volid': parameter_types.uuid_or_null,
        'consistencygroup_id': parameter_types.uuid_or_null,
        'os-vol-mig-status-attr:name_id': parameter_types.uuid_or_null,
        'name': {'type': ['string', 'null']},
        'bootable': {'type': 'string'},
        'created_at': parameter_types.date_time,
        'volume_type': {'type': ['string', 'null']},
        # TODO(zhufl): group_id is added in 3.13, we should move it to the
        # 3.13 schema file when microversion is supported in volume interfaces
        'group_id': parameter_types.uuid_or_null,
        # TODO(zhufl): provider_id is added in 3.21, we should move it to the
        # 3.21 schema file when microversion is supported in volume interfaces
        'provider_id': parameter_types.uuid_or_null,
        # TODO(zhufl): service_uuid and shared_targets are added in 3.48,
        # we should move them to the 3.48 schema file when microversion
        # is supported in volume interfaces.
        'service_uuid': parameter_types.uuid_or_null,
        'shared_targets': {'type': 'boolean'}
    },
    'additionalProperties': False,
    'required': ['attachments', 'links', 'encrypted',
                 'updated_at', 'replication_status', 'id',
                 'size', 'user_id', 'availability_zone',
                 'metadata', 'status', 'description',
                 'multiattach', 'consistencygroup_id',
                 'name', 'bootable', 'created_at',
                 'volume_type', 'snapshot_id', 'source_volid']
}

list_volumes_no_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volumes': {
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
                        # 'count': {'type': 'integer'}
                    },
                    'additionalProperties': False,
                    'required': ['links', 'id', 'name']
                }
            },
            'volumes_links': parameter_types.links
        },
        'additionalProperties': False,
        'required': ['volumes']
    }
}

show_volume = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volume': common_show_volume
        },
        'additionalProperties': False,
        'required': ['volume']
    }
}

list_volumes_detail = copy.deepcopy(common_show_volume)
# TODO(zhufl): count is added in 3.45, we should move it to the 3.45 schema
# file when microversion is supported in volume interfaces
# list_volumes_detail['properties'].update({'count': {'type': 'integer'}})
list_volumes_with_detail = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volumes': {
                'type': 'array',
                'items': list_volumes_detail
            },
            'volumes_links': parameter_types.links
        },
        'additionalProperties': False,
        'required': ['volumes']
    }
}

create_volume = {
    'status_code': [202],
    'response_body': {
        'type': 'object',
        'properties': {
            'volume': {
                'type': 'object',
                'properties': {
                    'migration_status': {'type': ['string', 'null']},
                    'attachments': attachments,
                    'links': parameter_types.links,
                    'availability_zone': {'type': ['string', 'null']},
                    'encrypted': {'type': 'boolean'},
                    'updated_at': parameter_types.date_time_or_null,
                    'replication_status': {'type': ['string', 'null']},
                    'snapshot_id': parameter_types.uuid_or_null,
                    'id': {'type': 'string', 'format': 'uuid'},
                    'size': {'type': 'integer'},
                    'user_id': {'type': 'string', 'format': 'uuid'},
                    'metadata': {'type': 'object'},
                    'status': {'type': 'string'},
                    'description': {'type': ['string', 'null']},
                    'multiattach': {'type': 'boolean'},
                    'source_volid': parameter_types.uuid_or_null,
                    'consistencygroup_id': parameter_types.uuid_or_null,
                    'name': {'type': ['string', 'null']},
                    'bootable': {'type': 'string'},
                    'created_at': parameter_types.date_time,
                    'volume_type': {'type': ['string', 'null']},
                    # TODO(zhufl): group_id is added in 3.13, we should move
                    # it to the 3.13 schema file when microversion is
                    # supported in volume interfaces.
                    'group_id': parameter_types.uuid_or_null,
                    # TODO(zhufl): provider_id is added in 3.21, we should
                    # move it to the 3.21 schema file when microversion is
                    # supported in volume interfaces
                    'provider_id': parameter_types.uuid_or_null,
                    # TODO(zhufl): service_uuid and shared_targets are added
                    # in 3.48, we should move them to the 3.48 schema file
                    # when microversion is supported in volume interfaces.
                    'service_uuid': parameter_types.uuid_or_null,
                    'shared_targets': {'type': 'boolean'}
                },
                'additionalProperties': False,
                'required': ['attachments', 'links', 'encrypted',
                             'updated_at', 'replication_status', 'id',
                             'size', 'user_id', 'availability_zone',
                             'metadata', 'status', 'description',
                             'multiattach', 'consistencygroup_id',
                             'name', 'bootable', 'created_at',
                             'volume_type', 'snapshot_id', 'source_volid']
            }
        },
        'additionalProperties': False,
        'required': ['volume']
    }
}

update_volume = copy.deepcopy(create_volume)
update_volume.update({'status_code': [200]})

delete_volume = {'status_code': [202]}

show_volume_summary = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'volume-summary': {
                'type': 'object',
                'properties': {
                    'total_size': {'type': 'integer'},
                    'total_count': {'type': 'integer'},
                    # TODO(zhufl): metadata is added in 3.36, we should move
                    # it to the 3.36 schema file when microversion is
                    # supported in volume interfaces
                    'metadata': {'type': 'object'},
                },
                'additionalProperties': False,
                'required': ['total_size', 'total_count']
            }
        },
        'additionalProperties': False,
        'required': ['volume-summary']
    }
}

# TODO(zhufl): This is under discussion, so will be merged in a seperate patch.
# https://bugs.launchpad.net/cinder/+bug/1880566
# upload_volume = {
#     'status_code': [202],
#     'response_body': {
#         'type': 'object',
#         'properties': {
#             'os-volume_upload_image': {
#                 'type': 'object',
#                 'properties': {
#                     'status': {'type': 'string'},
#                     'image_name': {'type': 'string'},
#                     'disk_format': {'type': 'string'},
#                     'container_format': {'type': 'string'},
#                     'is_public': {'type': 'boolean'},
#                     'visibility': {'type': 'string'},
#                     'protected': {'type': 'boolean'},
#                     'updated_at': parameter_types.date_time_or_null,
#                     'image_id': {'type': 'string', 'format': 'uuid'},
#                     'display_description': {'type': ['string', 'null']},
#                     'id': {'type': 'string', 'format': 'uuid'},
#                     'size': {'type': 'integer'},
#                     'volume_type': {
#                         'type': ['object', 'null'],
#                         'properties': {
#                             'created_at': parameter_types.date_time,
#                             'deleted': {'type': 'boolean'},
#                             'deleted_at': parameter_types.date_time_or_null,
#                             'description': {'type': ['string', 'null']},
#                             'extra_specs': {
#                                 'type': 'object',
#                                 'patternProperties': {
#                                     '^.+$': {'type': 'string'}
#                                 }
#                             },
#                             'id': {'type': 'string', 'format': 'uuid'},
#                             'is_public': {'type': 'boolean'},
#                             'name': {'type': ['string', 'null']},
#                             'qos_specs_id': parameter_types.uuid_or_null,
#                             'updated_at': parameter_types.date_time_or_null
#                         },
#                     }
#                 },
#                 'additionalProperties': False,
#                 'required': ['status', 'image_name', 'updated_at',
#                              'image_id',
#                              'display_description', 'id', 'size',
#                              'volume_type', 'disk_format',
#                              'container_format']
#             }
#         },
#         'additionalProperties': False,
#         'required': ['os-volume_upload_image']
#     }
# }

attach_volume = {'status_code': [202]}
set_bootable_volume = {'status_code': [200]}
detach_volume = {'status_code': [202]}
reserve_volume = {'status_code': [202]}
unreserve_volume = {'status_code': [202]}
extend_volume = {'status_code': [202]}
reset_volume_status = {'status_code': [202]}
update_volume_readonly = {'status_code': [202]}
force_delete_volume = {'status_code': [202]}
retype_volume = {'status_code': [202]}
force_detach_volume = {'status_code': [202]}

create_volume_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'metadata': {'type': 'object'},
        },
        'additionalProperties': False,
        'required': ['metadata']
    }
}

show_volume_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'metadata': {'type': 'object'},
        },
        'additionalProperties': False,
        'required': ['metadata']
    }
}
update_volume_metadata = copy.deepcopy(show_volume_metadata)

show_volume_metadata_item = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'meta': {'type': 'object'},
        },
        'additionalProperties': False,
        'required': ['meta']
    }
}
update_volume_metadata_item = copy.deepcopy(show_volume_metadata_item)
delete_volume_metadata_item = {'status_code': [200]}

update_volume_image_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {'metadata': {'type': 'object'}},
        'additionalProperties': False,
        'required': ['metadata']
    }
}
delete_volume_image_metadata = {'status_code': [200]}
show_volume_image_metadata = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'metadata': {'type': 'object'},
        },
        'additionalProperties': False,
        'required': ['metadata']
    }
}

unmanage_volume = {'status_code': [202]}
