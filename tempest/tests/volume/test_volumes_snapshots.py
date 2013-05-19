# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.test import attr
from tempest.tests.volume import base

LOG = logging.getLogger(__name__)


class VolumesSnapshotTest(base.BaseVolumeTest):
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(VolumesSnapshotTest, cls).setUpClass()
        try:
            cls.volume_origin = cls.create_volume()
        except Exception:
            LOG.exception("setup failed")
            cls.tearDownClass()
            raise

    @classmethod
    def tearDownClass(cls):
        super(VolumesSnapshotTest, cls).tearDownClass()

    @attr(type=['smoke'])
    def test_snapshot_create_get_delete(self):
        # Create a snapshot, get some of the details and then deletes it
        resp, snapshot = self.snapshots_client.create_snapshot(
            self.volume_origin['id'])
        self.assertEqual(200, resp.status)
        self.snapshots_client.wait_for_snapshot_status(snapshot['id'],
                                                       'available')
        errmsg = "Referred volume origin ID mismatch"
        self.assertEqual(self.volume_origin['id'],
                         snapshot['volume_id'],
                         errmsg)
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])

    @attr(type=['smoke'])
    def test_volume_from_snapshot(self):
        # Create a temporary snap using wrapper method from base, then
        # create a snap based volume, check resp code and deletes it
        snapshot = self.create_snapshot(self.volume_origin['id'])
        # NOTE: size is required also when passing snapshot_id
        resp, volume = self.volumes_client.create_volume(
            size=1,
            snapshot_id=snapshot['id'])
        self.assertEqual(200, resp.status)
        self.volumes_client.wait_for_volume_status(volume['id'], 'available')
        self.volumes_client.delete_volume(volume['id'])
        self.volumes_client.wait_for_resource_deletion(volume['id'])
        self.clear_snapshots()


class VolumesSnapshotTestXML(VolumesSnapshotTest):
    _interface = "xml"
