# Copyright 2013 Huawei Technologies Co.,LTD
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

from tempest.api.volume import base
from tempest import test


class VolumesActionsV2Test(base.BaseVolumeAdminTest):

    def _create_reset_and_force_delete_temp_volume(self, status=None):
        # Create volume, reset volume status, and force delete temp volume
        temp_volume = self.create_volume()
        if status:
            self.admin_volume_client.reset_volume_status(
                temp_volume['id'], status=status)
        self.admin_volume_client.force_delete_volume(temp_volume['id'])
        self.volumes_client.wait_for_resource_deletion(temp_volume['id'])

    @test.idempotent_id('d063f96e-a2e0-4f34-8b8a-395c42de1845')
    def test_volume_reset_status(self):
        # test volume reset status : available->error->available
        volume = self.create_volume()
        for status in ['error', 'available']:
            self.admin_volume_client.reset_volume_status(
                volume['id'], status=status)
            volume_get = self.admin_volume_client.show_volume(
                volume['id'])['volume']
            self.assertEqual(status, volume_get['status'])

    @test.idempotent_id('21737d5a-92f2-46d7-b009-a0cc0ee7a570')
    def test_volume_force_delete_when_volume_is_creating(self):
        # test force delete when status of volume is creating
        self._create_reset_and_force_delete_temp_volume('creating')

    @test.idempotent_id('db8d607a-aa2e-4beb-b51d-d4005c232011')
    def test_volume_force_delete_when_volume_is_attaching(self):
        # test force delete when status of volume is attaching
        self._create_reset_and_force_delete_temp_volume('attaching')

    @test.idempotent_id('3e33a8a8-afd4-4d64-a86b-c27a185c5a4a')
    def test_volume_force_delete_when_volume_is_error(self):
        # test force delete when status of volume is error
        self._create_reset_and_force_delete_temp_volume('error')


class VolumesActionsV1Test(VolumesActionsV2Test):
    _api_version = 1
