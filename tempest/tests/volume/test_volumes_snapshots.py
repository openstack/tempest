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

from tempest.common.utils.data_utils import rand_name
from tempest.tests.volume import base


class VolumesSnapshotTestBase(object):

    def test_volume_from_snapshot(self):
        volume_origin = self.create_volume(size=1)
        snapshot = self.create_snapshot(volume_origin['id'])
        volume_snap = self.create_volume(size=1,
                                         snapshot_id=
                                         snapshot['id'])
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.client.delete_volume(volume_snap['id'])
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])
        self.snapshots.remove(snapshot)
        self.client.delete_volume(volume_origin['id'])
        self.client.wait_for_resource_deletion(volume_snap['id'])
        self.volumes.remove(volume_snap)
        self.client.wait_for_resource_deletion(volume_origin['id'])
        self.volumes.remove(volume_origin)


class VolumesSnapshotTestXML(base.BaseVolumeTestXML,
                             VolumesSnapshotTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = "xml"
        super(VolumesSnapshotTestXML, cls).setUpClass()
        cls.client = cls.volumes_client


class VolumesSnapshotTestJSON(base.BaseVolumeTestJSON,
                              VolumesSnapshotTestBase):
    @classmethod
    def setUpClass(cls):
        cls._interface = "json"
        super(VolumesSnapshotTestJSON, cls).setUpClass()
        cls.client = cls.volumes_client
