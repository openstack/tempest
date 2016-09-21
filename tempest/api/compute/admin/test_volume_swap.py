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

from tempest.api.compute import base
from tempest.common import waiters
from tempest import config
from tempest import test

CONF = config.CONF


class TestVolumeSwap(base.BaseV2ComputeAdminTest):
    """The test suite for swapping of volume with admin user.

    The following is the scenario outline:
    1. Create a volume "volume1" with non-admin.
    2. Create a volume "volume2" with non-admin.
    3. Boot an instance "instance1" with non-admin.
    4. Attach "volume1" to "instance1" with non-admin.
    5. Swap volume from "volume1" to "volume2" as admin.
    6. Check the swap volume is successful and "volume2"
       is attached to "instance1" and "volume1" is in available state.
    """

    @classmethod
    def skip_checks(cls):
        super(TestVolumeSwap, cls).skip_checks()
        if not CONF.compute_feature_enabled.swap_volume:
            raise cls.skipException("Swapping volumes is not supported.")

    @classmethod
    def setup_clients(cls):
        super(TestVolumeSwap, cls).setup_clients()
        # We need the admin client for performing the update (swap) volume call
        cls.servers_admin_client = cls.os_adm.servers_client

    @test.idempotent_id('1769f00d-a693-4d67-a631-6a3496773813')
    @test.services('volume')
    def test_volume_swap(self):
        # Create two volumes.
        # NOTE(gmann): Volumes are created before server creation so that
        # volumes cleanup can happen successfully irrespective of which volume
        # is attached to server.
        volume1 = self.create_volume()
        volume2 = self.create_volume()
        # Boot server
        server = self.create_test_server(wait_until='ACTIVE')
        # Attach "volume1" to server
        self.attach_volume(server, volume1)
        # Swap volume from "volume1" to "volume2"
        self.servers_admin_client.update_attached_volume(
            server['id'], volume1['id'], volumeId=volume2['id'])
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume1['id'], 'available')
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume2['id'], 'in-use')
        self.addCleanup(self.servers_client.detach_volume,
                        server['id'], volume2['id'])
        # Verify "volume2" is attached to the server
        vol_attachments = self.servers_client.list_volume_attachments(
            server['id'])['volumeAttachments']
        self.assertEqual(1, len(vol_attachments))
        self.assertIn(volume2['id'], vol_attachments[0]['volumeId'])

        # TODO(mriedem): Test swapping back from volume2 to volume1 after
        # nova bug 1490236 is fixed.
