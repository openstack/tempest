# Copyright 2012 OpenStack Foundation
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

from tempest.openstack.common import log as logging
from tempest.test import attr
from tempest.thirdparty.boto.test import BotoTestCase

LOG = logging.getLogger(__name__)


def compare_volumes(a, b):
    return (a.id == b.id and
            a.size == b.size)


class EC2VolumesTest(BotoTestCase):

    @classmethod
    def setUpClass(cls):
        super(EC2VolumesTest, cls).setUpClass()
        cls.client = cls.os.ec2api_client
        cls.zone = cls.client.get_good_zone()

    @attr(type='smoke')
    def test_create_get_delete(self):
        # EC2 Create, get, delete Volume
        volume = self.client.create_volume(1, self.zone)
        cuk = self.addResourceCleanUp(self.client.delete_volume, volume.id)
        self.assertIn(volume.status, self.valid_volume_status)
        retrieved = self.client.get_all_volumes((volume.id,))
        self.assertEqual(1, len(retrieved))
        self.assertTrue(compare_volumes(volume, retrieved[0]))
        self.assertVolumeStatusWait(volume, "available")
        self.client.delete_volume(volume.id)
        self.cancelResourceCleanUp(cuk)

    @attr(type='smoke')
    def test_create_volume_from_snapshot(self):
        # EC2 Create volume from snapshot
        volume = self.client.create_volume(1, self.zone)
        self.addResourceCleanUp(self.client.delete_volume, volume.id)
        self.assertVolumeStatusWait(volume, "available")
        snap = self.client.create_snapshot(volume.id)
        self.addResourceCleanUp(self.destroy_snapshot_wait, snap)
        self.assertSnapshotStatusWait(snap, "completed")

        svol = self.client.create_volume(1, self.zone, snapshot=snap)
        cuk = self.addResourceCleanUp(svol.delete)
        self.assertVolumeStatusWait(svol, "available")
        svol.delete()
        self.cancelResourceCleanUp(cuk)
