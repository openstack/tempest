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

import time

from tempest.api.compute import base
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

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
    7. Swap volume from "volume2" to "volume1" as admin.
    8. Check the swap volume is successful and "volume1"
       is attached to "instance1" and "volume2" is in available state.
    """

    @classmethod
    def skip_checks(cls):
        super(TestVolumeSwap, cls).skip_checks()
        if not CONF.compute_feature_enabled.swap_volume:
            raise cls.skipException("Swapping volumes is not supported.")

    def _wait_for_server_volume_swap(self, server_id, old_volume_id,
                                     new_volume_id):
        """Waits for a server to swap the old volume to a new one."""
        volume_attachments = self.servers_client.list_volume_attachments(
            server_id)['volumeAttachments']
        attached_volume_ids = [attachment['volumeId']
                               for attachment in volume_attachments]
        start = int(time.time())

        while (old_volume_id in attached_volume_ids) \
                or (new_volume_id not in attached_volume_ids):
            time.sleep(self.servers_client.build_interval)
            volume_attachments = self.servers_client.list_volume_attachments(
                server_id)['volumeAttachments']
            attached_volume_ids = [attachment['volumeId']
                                   for attachment in volume_attachments]

            if int(time.time()) - start >= self.servers_client.build_timeout:
                old_vol_bdm_status = 'in BDM' \
                    if old_volume_id in attached_volume_ids else 'not in BDM'
                new_vol_bdm_status = 'in BDM' \
                    if new_volume_id in attached_volume_ids else 'not in BDM'
                message = ('Failed to swap old volume %(old_volume_id)s '
                           '(current %(old_vol_bdm_status)s) to new volume '
                           '%(new_volume_id)s (current %(new_vol_bdm_status)s)'
                           ' on server %(server_id)s within the required time '
                           '(%(timeout)s s)' %
                           {'old_volume_id': old_volume_id,
                            'old_vol_bdm_status': old_vol_bdm_status,
                            'new_volume_id': new_volume_id,
                            'new_vol_bdm_status': new_vol_bdm_status,
                            'server_id': server_id,
                            'timeout': self.servers_client.build_timeout})
                raise lib_exc.TimeoutException(message)

    @decorators.idempotent_id('1769f00d-a693-4d67-a631-6a3496773813')
    @utils.services('volume')
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
        self.admin_servers_client.update_attached_volume(
            server['id'], volume1['id'], volumeId=volume2['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume1['id'], 'available')
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume2['id'], 'in-use')
        self._wait_for_server_volume_swap(server['id'], volume1['id'],
                                          volume2['id'])
        # Verify "volume2" is attached to the server
        vol_attachments = self.servers_client.list_volume_attachments(
            server['id'])['volumeAttachments']
        self.assertEqual(1, len(vol_attachments))
        self.assertIn(volume2['id'], vol_attachments[0]['volumeId'])

        # Swap volume from "volume2" to "volume1"
        self.admin_servers_client.update_attached_volume(
            server['id'], volume2['id'], volumeId=volume1['id'])
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume2['id'], 'available')
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume1['id'], 'in-use')
        self._wait_for_server_volume_swap(server['id'], volume2['id'],
                                          volume1['id'])
        # Verify "volume1" is attached to the server
        vol_attachments = self.servers_client.list_volume_attachments(
            server['id'])['volumeAttachments']
        self.assertEqual(1, len(vol_attachments))
        self.assertIn(volume1['id'], vol_attachments[0]['volumeId'])
