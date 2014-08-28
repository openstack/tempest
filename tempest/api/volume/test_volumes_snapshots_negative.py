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

import uuid

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class VolumesSnapshotNegativeTest(base.BaseVolumeV1Test):
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(VolumesSnapshotNegativeTest, cls).setUpClass()

        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    @test.attr(type=['negative', 'gate'])
    def test_create_snapshot_with_nonexistent_volume_id(self):
        # Create a snapshot with nonexistent volume id
        s_name = data_utils.rand_name('snap')
        self.assertRaises(exceptions.NotFound,
                          self.snapshots_client.create_snapshot,
                          str(uuid.uuid4()), display_name=s_name)

    @test.attr(type=['negative', 'gate'])
    def test_create_snapshot_without_passing_volume_id(self):
        # Create a snapshot without passing volume id
        s_name = data_utils.rand_name('snap')
        self.assertRaises(exceptions.NotFound,
                          self.snapshots_client.create_snapshot,
                          None, display_name=s_name)

    @test.attr(type=['negative', 'gate'])
    def test_get_snapshot_with_nonexistent_snapshot_id(self):
        # Should not be able to get snapshot with nonexistent snapshot id.
        self.assertRaises(exceptions.NotFound,
                          self.snapshots_client.get_snapshot,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    def test_delete_snapshot_with_nonexistent_snapshot_id(self):
        # Should not be able to delete snapshot with nonexistent snapshot id.
        self.assertRaises(exceptions.NotFound,
                          self.snapshots_client.delete_snapshot,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    def test_update_snapshot_with_nonexistent_snapshot_id(self):
        # Should not be able to update snapshot with nonexistent snapshot id.
        self.assertRaises(exceptions.NotFound,
                          self.snapshots_client.update_snapshot,
                          str(uuid.uuid4()))

    @test.attr(type=['negative', 'gate'])
    def test_list_snapshot_with_nonexistent_name(self):
        snap_name = data_utils.rand_name('snap-')
        params = {'display_name': snap_name}
        resp, fetched_snap = self.snapshots_client.list_snapshots(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(fetched_snap))

    @test.attr(type=['negative', 'gate'])
    def test_list_snapshot_detail_with_nonexistent_name(self):
        snap_name = data_utils.rand_name('snap-')
        params = {'display_name': snap_name}
        resp, fetched_snap = self.snapshots_client.list_snapshots_with_detail(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(fetched_snap))


class VolumesSnapshotV2NegativeTest(VolumesSnapshotNegativeTest):
    _api_version= 2


class VolumesSnapshotNegativeTestXML(VolumesSnapshotNegativeTest):
    _interface = "xml"
