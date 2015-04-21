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

from testtools import matchers

from tempest.api.volume import base
from tempest import clients
from tempest.common import credentials
from tempest import config
from tempest import test

CONF = config.CONF


class VolumesV2TransfersTest(base.BaseVolumeTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesV2TransfersTest, cls).skip_checks()
        if not credentials.is_admin_available():
            msg = "Missing Volume Admin API credentials in configuration."
            raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        super(VolumesV2TransfersTest, cls).setup_credentials()
        # Add another tenant to test volume-transfer
        cls.os_alt = clients.Manager(cls.isolated_creds.get_alt_creds())
        # Add admin tenant to cleanup resources
        creds = cls.isolated_creds.get_admin_creds()
        cls.os_adm = clients.Manager(credentials=creds)

    @classmethod
    def setup_clients(cls):
        super(VolumesV2TransfersTest, cls).setup_clients()

        cls.client = cls.volumes_client
        cls.alt_client = cls.os_alt.volumes_client
        cls.alt_tenant_id = cls.alt_client.tenant_id
        cls.adm_client = cls.os_adm.volumes_client

    def _delete_volume(self, volume_id):
        # Delete the specified volume using admin creds
        self.adm_client.delete_volume(volume_id)
        self.adm_client.wait_for_resource_deletion(volume_id)

    @test.attr(type='gate')
    @test.idempotent_id('4d75b645-a478-48b1-97c8-503f64242f1a')
    def test_create_get_list_accept_volume_transfer(self):
        # Create a volume first
        volume = self.create_volume()
        self.addCleanup(self._delete_volume, volume['id'])

        # Create a volume transfer
        transfer = self.client.create_volume_transfer(volume['id'])
        transfer_id = transfer['id']
        auth_key = transfer['auth_key']
        self.client.wait_for_volume_status(volume['id'],
                                           'awaiting-transfer')

        # Get a volume transfer
        body = self.client.show_volume_transfer(transfer_id)
        self.assertEqual(volume['id'], body['volume_id'])

        # List volume transfers, the result should be greater than
        # or equal to 1
        body = self.client.list_volume_transfers()
        self.assertThat(len(body), matchers.GreaterThan(0))

        # Accept a volume transfer by alt_tenant
        body = self.alt_client.accept_volume_transfer(transfer_id,
                                                      auth_key)
        self.alt_client.wait_for_volume_status(volume['id'], 'available')

    @test.idempotent_id('ab526943-b725-4c07-b875-8e8ef87a2c30')
    def test_create_list_delete_volume_transfer(self):
        # Create a volume first
        volume = self.create_volume()
        self.addCleanup(self._delete_volume, volume['id'])

        # Create a volume transfer
        body = self.client.create_volume_transfer(volume['id'])
        transfer_id = body['id']
        self.client.wait_for_volume_status(volume['id'],
                                           'awaiting-transfer')

        # List all volume transfers (looking for the one we created)
        body = self.client.list_volume_transfers()
        for transfer in body:
            if volume['id'] == transfer['volume_id']:
                break
        else:
            self.fail('Transfer not found for volume %s' % volume['id'])

        # Delete a volume transfer
        self.client.delete_volume_transfer(transfer_id)
        self.client.wait_for_volume_status(volume['id'], 'available')


class VolumesV1TransfersTest(VolumesV2TransfersTest):
    _api_version = 1
