# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest import clients
from tempest.test import attr


class VolumesTransfersTest(base.BaseVolumeV1Test):
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(VolumesTransfersTest, cls).setUpClass()

        # Add another tenant to test volume-transfer
        if cls.config.compute.allow_tenant_isolation:
            creds = cls.isolated_creds.get_alt_creds()
            username, tenant_name, password = creds
            cls.os_alt = clients.Manager(username=username,
                                         password=password,
                                         tenant_name=tenant_name,
                                         interface=cls._interface)
            cls.alt_tenant_id = cls.isolated_creds.get_alt_tenant()['id']

            # Add admin tenant to cleanup resources
            adm_creds = cls.isolated_creds.get_admin_creds()
            admin_username, admin_tenant_name, admin_password = adm_creds
            cls.os_adm = clients.Manager(username=admin_username,
                                         password=admin_password,
                                         tenant_name=admin_tenant_name,
                                         interface=cls._interface)
        else:
            cls.os_alt = clients.AltManager()
            alt_tenant_name = cls.os_alt.tenant_name
            identity_client = cls._get_identity_admin_client()
            _, tenants = identity_client.list_tenants()
            cls.alt_tenant_id = [tnt['id'] for tnt in tenants
                                 if tnt['name'] == alt_tenant_name][0]
            cls.os_adm = clients.ComputeAdminManager(interface=cls._interface)

        cls.client = cls.volumes_client
        cls.alt_client = cls.os_alt.volumes_client
        cls.adm_client = cls.os_adm.volumes_client

    @attr(type='gate')
    def test_create_get_list_accept_volume_transfer(self):
        # Create a volume first
        volume = self.create_volume()

        # Create a volume transfer
        resp, transfer = self.client.create_volume_transfer(volume['id'])
        self.assertEqual(202, resp.status)
        transfer_id = transfer['id']
        auth_key = transfer['auth_key']
        self.client.wait_for_volume_status(volume['id'],
                                           'awaiting-transfer')

        # Get a volume transfer
        resp, body = self.client.get_volume_transfer(transfer_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(volume['id'], body['volume_id'])

        # List volume transfers, the result should be greater than
        # or equal to 1
        resp, body = self.client.list_volume_transfers()
        self.assertEqual(200, resp.status)
        self.assertGreaterEqual(len(body), 1)

        # Accept a volume transfer by alt_tenant
        resp, body = self.alt_client.accept_volume_transfer(transfer_id,
                                                            auth_key)
        self.assertEqual(202, resp.status)
        self.alt_client.wait_for_volume_status(volume['id'], 'available')

    def test_create_list_delete_volume_transfer(self):
        # Create a volume first
        volume = self.create_volume()

        # Create a volume transfer
        resp, body = self.client.create_volume_transfer(volume['id'])
        self.assertEqual(202, resp.status)
        transfer_id = body['id']
        self.client.wait_for_volume_status(volume['id'],
                                           'awaiting-transfer')

        # List all volume transfers, there's only one in this test
        resp, body = self.client.list_volume_transfers()
        self.assertEqual(200, resp.status)
        self.assertEqual(volume['id'], body[0]['volume_id'])

        # Delete a volume transfer
        resp, body = self.client.delete_volume_transfer(transfer_id)
        self.assertEqual(202, resp.status)
        self.client.wait_for_volume_status(volume['id'], 'available')


class VolumesTransfersTestXML(VolumesTransfersTest):
    _interface = "xml"
