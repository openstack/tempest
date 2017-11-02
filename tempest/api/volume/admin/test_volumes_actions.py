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
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class VolumesActionsTest(base.BaseVolumeAdminTest):

    def _create_reset_and_force_delete_temp_volume(self, status=None):
        # Create volume, reset volume status, and force delete temp volume
        temp_volume = self.create_volume()
        if status:
            self.admin_volume_client.reset_volume_status(
                temp_volume['id'], status=status)
            waiters.wait_for_volume_resource_status(
                self.volumes_client, temp_volume['id'], status)
        self.admin_volume_client.force_delete_volume(temp_volume['id'])
        self.volumes_client.wait_for_resource_deletion(temp_volume['id'])

    @decorators.idempotent_id('d063f96e-a2e0-4f34-8b8a-395c42de1845')
    def test_volume_reset_status(self):
        # test volume reset status : available->error->available->maintenance
        volume = self.create_volume()
        self.addCleanup(waiters.wait_for_volume_resource_status,
                        self.volumes_client, volume['id'], 'available')
        self.addCleanup(self.admin_volume_client.reset_volume_status,
                        volume['id'], status='available')
        for status in ['error', 'available', 'maintenance']:
            self.admin_volume_client.reset_volume_status(
                volume['id'], status=status)
            waiters.wait_for_volume_resource_status(
                self.volumes_client, volume['id'], status)

    @decorators.idempotent_id('21737d5a-92f2-46d7-b009-a0cc0ee7a570')
    def test_volume_force_delete_when_volume_is_creating(self):
        # test force delete when status of volume is creating
        self._create_reset_and_force_delete_temp_volume('creating')

    @decorators.idempotent_id('db8d607a-aa2e-4beb-b51d-d4005c232011')
    def test_volume_force_delete_when_volume_is_attaching(self):
        # test force delete when status of volume is attaching
        self._create_reset_and_force_delete_temp_volume('attaching')

    @decorators.idempotent_id('3e33a8a8-afd4-4d64-a86b-c27a185c5a4a')
    def test_volume_force_delete_when_volume_is_error(self):
        # test force delete when status of volume is error
        self._create_reset_and_force_delete_temp_volume('error')

    @decorators.idempotent_id('b957cabd-1486-4e21-90cf-a9ed3c39dfb2')
    def test_volume_force_delete_when_volume_is_maintenance(self):
        # test force delete when status of volume is maintenance
        self._create_reset_and_force_delete_temp_volume('maintenance')

    @decorators.idempotent_id('d38285d9-929d-478f-96a5-00e66a115b81')
    @utils.services('compute')
    def test_force_detach_volume(self):
        # Create a server and a volume
        server_id = self.create_server()['id']
        volume_id = self.create_volume()['id']

        # Attach volume
        self.volumes_client.attach_volume(
            volume_id,
            instance_uuid=server_id,
            mountpoint='/dev/%s' % CONF.compute.volume_device_name)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume_id, 'in-use')
        self.addCleanup(waiters.wait_for_volume_resource_status,
                        self.volumes_client, volume_id, 'available')
        self.addCleanup(self.volumes_client.detach_volume, volume_id)
        attachment = self.volumes_client.show_volume(
            volume_id)['volume']['attachments'][0]

        # Reset volume's status to error
        self.admin_volume_client.reset_volume_status(volume_id, status='error')
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume_id, 'error')

        # Force detach volume
        self.admin_volume_client.force_detach_volume(
            volume_id, connector=None,
            attachment_id=attachment['attachment_id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume_id, 'available')
        vol_info = self.volumes_client.show_volume(volume_id)['volume']
        self.assertIn('attachments', vol_info)
        self.assertEmpty(vol_info['attachments'])
