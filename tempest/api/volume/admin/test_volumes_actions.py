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

from tempest_lib.common.utils import data_utils as utils

from tempest.api.volume import base
from tempest import test


class VolumesActionsV2Test(base.BaseVolumeAdminTest):

    @classmethod
    def setup_clients(cls):
        super(VolumesActionsV2Test, cls).setup_clients()
        cls.client = cls.volumes_client

    @classmethod
    def resource_setup(cls):
        super(VolumesActionsV2Test, cls).resource_setup()

        # Create a test shared volume for tests
        vol_name = utils.rand_name(cls.__name__ + '-Volume')
        cls.name_field = cls.special_fields['name_field']
        params = {cls.name_field: vol_name}

        cls.volume = cls.client.create_volume(**params)
        cls.client.wait_for_volume_status(cls.volume['id'], 'available')

    @classmethod
    def resource_cleanup(cls):
        # Delete the test volume
        cls.client.delete_volume(cls.volume['id'])
        cls.client.wait_for_resource_deletion(cls.volume['id'])

        super(VolumesActionsV2Test, cls).resource_cleanup()

    def _reset_volume_status(self, volume_id, status):
        # Reset the volume status
        body = self.admin_volume_client.reset_volume_status(volume_id,
                                                            status)
        return body

    def tearDown(self):
        # Set volume's status to available after test
        self._reset_volume_status(self.volume['id'], 'available')
        super(VolumesActionsV2Test, self).tearDown()

    def _create_temp_volume(self):
        # Create a temp volume for force delete tests
        vol_name = utils.rand_name('Volume')
        params = {self.name_field: vol_name}
        temp_volume = self.client.create_volume(**params)
        self.client.wait_for_volume_status(temp_volume['id'], 'available')

        return temp_volume

    def _create_reset_and_force_delete_temp_volume(self, status=None):
        # Create volume, reset volume status, and force delete temp volume
        temp_volume = self._create_temp_volume()
        if status:
            self._reset_volume_status(temp_volume['id'], status)
        self.admin_volume_client.force_delete_volume(temp_volume['id'])
        self.client.wait_for_resource_deletion(temp_volume['id'])

    @test.attr(type='gate')
    @test.idempotent_id('d063f96e-a2e0-4f34-8b8a-395c42de1845')
    def test_volume_reset_status(self):
        # test volume reset status : available->error->available
        self._reset_volume_status(self.volume['id'], 'error')
        volume_get = self.admin_volume_client.show_volume(
            self.volume['id'])
        self.assertEqual('error', volume_get['status'])

    @test.idempotent_id('21737d5a-92f2-46d7-b009-a0cc0ee7a570')
    def test_volume_force_delete_when_volume_is_creating(self):
        # test force delete when status of volume is creating
        self._create_reset_and_force_delete_temp_volume('creating')

    @test.idempotent_id('db8d607a-aa2e-4beb-b51d-d4005c232011')
    def test_volume_force_delete_when_volume_is_attaching(self):
        # test force delete when status of volume is attaching
        self._create_reset_and_force_delete_temp_volume('attaching')

    @test.attr(type='gate')
    @test.idempotent_id('3e33a8a8-afd4-4d64-a86b-c27a185c5a4a')
    def test_volume_force_delete_when_volume_is_error(self):
        # test force delete when status of volume is error
        self._create_reset_and_force_delete_temp_volume('error')


class VolumesActionsV1Test(VolumesActionsV2Test):
    _api_version = 1
