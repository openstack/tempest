# Copyright 2022 Red Hat, Inc.
# All Rights Reserved.
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
from tempest.lib.api_schema.response.volume import backups

# Volume micro version 3.64:
# 1. Include the encryption_key_id in volume and backup
# details when the associated volume is encrypted.
# https://docs.openstack.org/cinder/latest/contributor/
# api_microversion_history.html

common_show_backup = copy.deepcopy(backups.common_show_backup)
common_show_backup['properties'].update(
    {'encryption_key_id': parameter_types.uuid_or_null})

create_backup = copy.deepcopy(backups.create_backup)
update_backup = copy.deepcopy(backups.update_backup)
restore_backup = copy.deepcopy(backups.restore_backup)
delete_backup = copy.deepcopy(backups.delete_backup)
# show backup refers to common_show_backup
show_backup = copy.deepcopy(backups.show_backup)
show_backup['response_body']['properties']['backup'] = common_show_backup
list_backups_no_detail = copy.deepcopy(backups.list_backups_no_detail)
# list_backups_detail refers to latest common_show_backup
list_backups_detail = copy.deepcopy(common_show_backup)
list_backups_detail['properties'].update({'count': {'type': 'integer'}})
list_backups_with_detail = copy.deepcopy(backups.list_backups_with_detail)
# list_backups_with_detail refers to latest list_backups_detail
list_backups_with_detail['response_body']['properties']['backups']['items'] =\
    list_backups_detail
export_backup = copy.deepcopy(backups.export_backup)
import_backup = copy.deepcopy(backups.import_backup)
reset_backup_status = copy.deepcopy(backups.reset_backup_status)
