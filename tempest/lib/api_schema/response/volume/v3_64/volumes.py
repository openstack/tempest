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
from tempest.lib.api_schema.response.volume.v3_63 import volumes

# Volume micro version 3.64:
# 1. Include the encryption_key_id in volume and backup
# details when the associated volume is encrypted.
# https://docs.openstack.org/cinder/latest/contributor/
# api_microversion_history.html

common_show_volume = copy.deepcopy(volumes.common_show_volume)
common_show_volume['properties'].update(
    {'encryption_key_id': parameter_types.uuid_or_null})

create_volume = copy.deepcopy(volumes.create_volume)
create_volume['response_body']['properties']['volume']['properties'].update(
    {'encryption_key_id': parameter_types.uuid_or_null})

# copy unchanged volumes schema
attachments = copy.deepcopy(volumes.attachments)
list_volumes_no_detail = copy.deepcopy(volumes.list_volumes_no_detail)
# show_volume refers to common_show_volume
show_volume = copy.deepcopy(volumes.show_volume)
show_volume['response_body']['properties']['volume'] = common_show_volume
# list_volumes_detail refers to latest common_show_volume
list_volumes_detail = copy.deepcopy(common_show_volume)
list_volumes_with_detail = copy.deepcopy(volumes.list_volumes_with_detail)
list_volumes_with_detail['response_body']['properties']['volumes']['items'] \
    = list_volumes_detail
update_volume = copy.deepcopy(volumes.update_volume)
delete_volume = copy.deepcopy(volumes.delete_volume)
show_volume_summary = copy.deepcopy(volumes.show_volume_summary)
attach_volume = copy.deepcopy(volumes.attach_volume)
set_bootable_volume = copy.deepcopy(volumes.set_bootable_volume)
detach_volume = copy.deepcopy(volumes.detach_volume)
reserve_volume = copy.deepcopy(volumes.reserve_volume)
unreserve_volume = copy.deepcopy(volumes.unreserve_volume)
extend_volume = copy.deepcopy(volumes.extend_volume)
reset_volume_status = copy.deepcopy(volumes.reset_volume_status)
update_volume_readonly = copy.deepcopy(volumes.update_volume_readonly)
force_delete_volume = copy.deepcopy(volumes.force_delete_volume)
retype_volume = copy.deepcopy(volumes.retype_volume)
force_detach_volume = copy.deepcopy(volumes.force_detach_volume)
create_volume_metadata = copy.deepcopy(volumes.create_volume_metadata)
show_volume_metadata = copy.deepcopy(volumes.show_volume_metadata)
update_volume_metadata = copy.deepcopy(volumes.update_volume_metadata)
update_volume_metadata_item = copy.deepcopy(
    volumes.update_volume_metadata_item)
update_volume_image_metadata = copy.deepcopy(
    volumes.update_volume_image_metadata)
delete_volume_image_metadata = copy.deepcopy(
    volumes.delete_volume_image_metadata)
unmanage_volume = copy.deepcopy(volumes.unmanage_volume)
