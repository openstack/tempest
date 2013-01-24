# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import logging
import time

from nose.plugins.attrib import attr
import testtools

from tempest import clients
from tempest.testboto import BotoTestCase

LOG = logging.getLogger(__name__)


def compare_volumes(a, b):
    return (a.id == b.id and
            a.size == b.size)


@attr("EC2")
class EC2VolumesTest(BotoTestCase):

    @classmethod
    def setUpClass(cls):
        super(EC2VolumesTest, cls).setUpClass()
        cls.os = clients.Manager()
        cls.client = cls.os.ec2api_client
        cls.zone = cls.client.get_good_zone()

#NOTE(afazekas): as admin it can trigger the Bug #1074901
    @attr(type='smoke')
    def test_create_get_delete(self):
        # EC2 Create, get, delete Volume
        volume = self.client.create_volume(1, self.zone)
        cuk = self.addResourceCleanUp(self.client.delete_volume, volume.id)
        self.assertIn(volume.status, self.valid_volume_status)
        retrieved = self.client.get_all_volumes((volume.id,))
        self.assertEqual(1, len(retrieved))
        self.assertTrue(compare_volumes(volume, retrieved[0]))

        def _status():
            volume.update(validate=True)
            return volume.status

        self.assertVolumeStatusWait(_status, "available")
        self.client.delete_volume(volume.id)
        self.cancelResourceCleanUp(cuk)

    @attr(type='smoke')
    def test_create_volume_from_snapshot(self):
        # EC2 Create volume from snapshot
        volume = self.client.create_volume(1, self.zone)
        self.addResourceCleanUp(self.client.delete_volume, volume.id)

        def _status():
            volume.update(validate=True)
            return volume.status

        self.assertVolumeStatusWait(_status, "available")
        snap = self.client.create_snapshot(volume.id)
        self.addResourceCleanUp(self.destroy_snapshot_wait, snap)

        def _snap_status():
            snap.update(validate=True)
            return snap.status

        self.assertSnapshotStatusWait(_snap_status, "completed")

        svol = self.client.create_volume(1, self.zone, snapshot=snap)
        cuk = self.addResourceCleanUp(svol.delete)

        def _snap_vol_status():
            svol.update(validate=True)
            return svol.status

        self.assertVolumeStatusWait(_snap_vol_status, "available")
        svol.delete()
        self.cancelResourceCleanUp(cuk)
