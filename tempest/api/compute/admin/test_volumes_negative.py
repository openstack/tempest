# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.api.compute import base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class VolumesAdminNegativeTest(base.BaseV2ComputeAdminTest):
    """Negative tests of volume swapping"""

    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(VolumesAdminNegativeTest, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def resource_setup(cls):
        super(VolumesAdminNegativeTest, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until='ACTIVE')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('309b5ecd-0585-4a7e-a36f-d2b2bf55259d')
    def test_update_attached_volume_with_nonexistent_volume_in_uri(self):
        """Test swapping non existent volume should fail"""
        volume = self.create_volume()
        nonexistent_volume = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.admin_servers_client.update_attached_volume,
                          self.server['id'], nonexistent_volume,
                          volumeId=volume['id'])

    @decorators.related_bug('1629110', status_code=400)
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7dcac15a-b107-46d3-a5f6-cb863f4e454a')
    def test_update_attached_volume_with_nonexistent_volume_in_body(self):
        """Test swapping volume to a non existence volume should fail"""
        volume = self.create_volume()
        self.attach_volume(self.server, volume)

        nonexistent_volume = data_utils.rand_uuid()
        self.assertRaises(lib_exc.BadRequest,
                          self.admin_servers_client.update_attached_volume,
                          self.server['id'], volume['id'],
                          volumeId=nonexistent_volume)


class UpdateMultiattachVolumeNegativeTest(base.BaseV2ComputeAdminTest):
    """Negative tests of swapping volume attached to multiple servers

    Negative tests of swapping volume attached to multiple servers with
    compute microversion greater than 2.59 and volume microversion greater
    than 3.26
    """

    min_microversion = '2.60'
    volume_min_microversion = '3.27'

    @classmethod
    def skip_checks(cls):
        super(UpdateMultiattachVolumeNegativeTest, cls).skip_checks()
        if not CONF.compute_feature_enabled.volume_multiattach:
            raise cls.skipException('Volume multi-attach is not available.')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7576d497-b7c6-44bd-9cc5-c5b4e50fec71')
    @utils.services('volume')
    def test_multiattach_rw_volume_update_failure(self):
        """Test swapping volume attached to multi-servers with read-write mode

        1. Create two volumes "vol1" and "vol2"
        2. Create two instances "server1" and "server2"
        3. Attach "vol1" to both of these instances
        4. By default both of these attachments should have an attach_mode of
           read-write, so trying to swap "vol1" to "vol2" should fail
        5. Check "vol1" is still attached to both servers
        6. Check "vol2" is not attached to any server
        """
        # Create two multiattach capable volumes.
        vol1 = self.create_volume(multiattach=True)
        vol2 = self.create_volume(multiattach=True)

        # Create two instances.
        server1 = self.create_test_server(wait_until='ACTIVE')
        server2 = self.create_test_server(wait_until='ACTIVE')

        # Attach vol1 to both of these instances.
        vol1_attachment1 = self.attach_volume(server1, vol1)
        vol1_attachment2 = self.attach_volume(server2, vol1)

        # Assert that we now have two attachments.
        vol1 = self.volumes_client.show_volume(vol1['id'])['volume']
        self.assertEqual(2, len(vol1['attachments']))

        # By default both of these attachments should have an attach_mode of
        # read-write, assert that here to ensure the following calls to update
        # the volume will be rejected.
        for volume_attachment in vol1['attachments']:
            attachment_id = volume_attachment['attachment_id']
            attachment = self.attachments_client.show_attachment(
                attachment_id)['attachment']
            self.assertEqual('rw', attachment['attach_mode'])

        # Assert that a BadRequest is raised when we attempt to update volume1
        # to volume2 on server1 or server2.
        self.assertRaises(lib_exc.BadRequest,
                          self.admin_servers_client.update_attached_volume,
                          server1['id'], vol1['id'], volumeId=vol2['id'])
        self.assertRaises(lib_exc.BadRequest,
                          self.admin_servers_client.update_attached_volume,
                          server2['id'], vol1['id'], volumeId=vol2['id'])

        # Fetch the volume 1 to check the current attachments.
        vol1 = self.volumes_client.show_volume(vol1['id'])['volume']
        vol1_attachment_ids = [a['id'] for a in vol1['attachments']]

        # Assert that volume 1 is still attached to both server 1 and 2.
        self.assertIn(vol1_attachment1['id'], vol1_attachment_ids)
        self.assertIn(vol1_attachment2['id'], vol1_attachment_ids)

        # Assert that volume 2 has no attachments.
        vol2 = self.volumes_client.show_volume(vol2['id'])['volume']
        self.assertEqual([], vol2['attachments'])
