# Copyright 2013 OpenStack Foundation
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
from tempest.common import waiters
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators


class VolumesTransfersTest(base.BaseVolumeTest):

    credentials = ['primary', 'alt', 'admin']

    @classmethod
    def setup_clients(cls):
        super(VolumesTransfersTest, cls).setup_clients()

        cls.client = cls.os_primary.volume_transfers_client_latest
        cls.alt_client = cls.os_alt.volume_transfers_client_latest
        cls.alt_volumes_client = cls.os_alt.volumes_client_latest
        cls.adm_volumes_client = cls.os_admin.volumes_client_latest

    @decorators.idempotent_id('4d75b645-a478-48b1-97c8-503f64242f1a')
    def test_create_get_list_accept_volume_transfer(self):
        # Create a volume first
        volume = self.create_volume()
        self.addCleanup(self.delete_volume,
                        self.adm_volumes_client,
                        volume['id'])

        # Create a volume transfer
        transfer = self.client.create_volume_transfer(
            volume_id=volume['id'])['transfer']
        transfer_id = transfer['id']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.client.delete_volume_transfer,
                        transfer_id)
        auth_key = transfer['auth_key']
        waiters.wait_for_volume_resource_status(
            self.volumes_client, volume['id'], 'awaiting-transfer')

        # Get a volume transfer
        body = self.client.show_volume_transfer(transfer_id)['transfer']
        self.assertEqual(volume['id'], body['volume_id'])

        # List volume transfers, the result should be greater than
        # or equal to 1
        body = self.client.list_volume_transfers()['transfers']
        self.assertNotEmpty(body)

        # Accept a volume transfer by alt_tenant
        body = self.alt_client.accept_volume_transfer(
            transfer_id, auth_key=auth_key)['transfer']
        waiters.wait_for_volume_resource_status(self.alt_volumes_client,
                                                volume['id'], 'available')
        accepted_volume = self.alt_volumes_client.show_volume(
            volume['id'])['volume']
        self.assertEqual(self.os_alt.credentials.user_id,
                         accepted_volume['user_id'])
        self.assertEqual(self.os_alt.credentials.project_id,
                         accepted_volume['os-vol-tenant-attr:tenant_id'])

    @decorators.idempotent_id('ab526943-b725-4c07-b875-8e8ef87a2c30')
    def test_create_list_delete_volume_transfer(self):
        # Create a volume first
        volume = self.create_volume()
        self.addCleanup(self.delete_volume,
                        self.adm_volumes_client,
                        volume['id'])

        # Create a volume transfer
        transfer_id = self.client.create_volume_transfer(
            volume_id=volume['id'])['transfer']['id']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.client.delete_volume_transfer,
                        transfer_id)
        waiters.wait_for_volume_resource_status(
            self.volumes_client, volume['id'], 'awaiting-transfer')

        # List all volume transfers with details, check the detail-specific
        # elements, and look for the created transfer.
        transfers = self.client.list_volume_transfers(detail=True)['transfers']
        self.assertNotEmpty(transfers)
        volume_list = [transfer['volume_id'] for transfer in transfers]
        self.assertIn(volume['id'], volume_list,
                      'Transfer not found for volume %s' % volume['id'])

        # Delete a volume transfer
        self.client.delete_volume_transfer(transfer_id)
        waiters.wait_for_volume_resource_status(
            self.volumes_client, volume['id'], 'available')
