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

from tempest.api.volume import base
from tempest.common.utils.data_utils import rand_name
from tempest.openstack.common import log as logging
from tempest.test import attr

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

    @attr(type='gate')
    def test_snapshot_create_get_list_update_delete(self):
        # Create a snapshot
        s_name = rand_name('snap')
        snapshot = self.create_snapshot(self.volume_origin['id'],
                                        display_name=s_name)

        # Get the snap and check for some of its details
        resp, snap_get = self.snapshots_client.get_snapshot(snapshot['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(self.volume_origin['id'],
                         snap_get['volume_id'],
                         "Referred volume origin mismatch")

        # Compare also with the output from the list action
        tracking_data = (snapshot['id'], snapshot['display_name'])
        resp, snaps_list = self.snapshots_client.list_snapshots()
        self.assertEqual(200, resp.status)
        snaps_data = [(f['id'], f['display_name']) for f in snaps_list]
        self.assertIn(tracking_data, snaps_data)

        # Updates snapshot with new values
        new_s_name = rand_name('new-snap')
        new_desc = 'This is the new description of snapshot.'
        resp, update_snapshot = \
            self.snapshots_client.update_snapshot(snapshot['id'],
                                                  display_name=new_s_name,
                                                  display_description=new_desc)
        # Assert response body for update_snapshot method
        self.assertEqual(200, resp.status)
        self.assertEqual(new_s_name, update_snapshot['display_name'])
        self.assertEqual(new_desc, update_snapshot['display_description'])
        # Assert response body for get_snapshot method
        resp, updated_snapshot = \
            self.snapshots_client.get_snapshot(snapshot['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(new_s_name, updated_snapshot['display_name'])
        self.assertEqual(new_desc, updated_snapshot['display_description'])

        # Delete the snapshot
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.assertEqual(200, resp.status)
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])
        self.snapshots.remove(snapshot)

    @attr(type='gate')
    def test_volume_from_snapshot(self):
        # Create a temporary snap using wrapper method from base, then
        # create a snap based volume, check resp code and deletes it
        snapshot = self.create_snapshot(self.volume_origin['id'])
        # NOTE(gfidente): size is required also when passing snapshot_id
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
