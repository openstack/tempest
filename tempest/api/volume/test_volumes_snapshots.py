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
from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
from tempest import test

LOG = logging.getLogger(__name__)
CONF = config.CONF


class VolumesSnapshotTest(base.BaseVolumeV1Test):
    _interface = "json"

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(VolumesSnapshotTest, cls).setUpClass()
        cls.volume_origin = cls.create_volume()

        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    @classmethod
    def tearDownClass(cls):
        super(VolumesSnapshotTest, cls).tearDownClass()

    def _detach(self, volume_id):
        """Detach volume."""
        self.volumes_client.detach_volume(volume_id)
        self.volumes_client.wait_for_volume_status(volume_id, 'available')

    def _list_by_param_values_and_assert(self, params, with_detail=False):
        """
        Perform list or list_details action with given params
        and validates result.
        """
        if with_detail:
            _, fetched_snap_list = \
                self.snapshots_client.\
                list_snapshots_with_detail(params=params)
        else:
            _, fetched_snap_list = \
                self.snapshots_client.list_snapshots(params=params)

        # Validating params of fetched snapshots
        for snap in fetched_snap_list:
            for key in params:
                msg = "Failed to list snapshots %s by %s" % \
                      ('details' if with_detail else '', key)
                self.assertEqual(params[key], snap[key], msg)

    @test.attr(type='gate')
    @test.services('compute')
    def test_snapshot_create_with_volume_in_use(self):
        # Create a snapshot when volume status is in-use
        # Create a test instance
        server_name = data_utils.rand_name('instance-')
        resp, server = self.servers_client.create_server(server_name,
                                                         self.image_ref,
                                                         self.flavor_ref)
        self.addCleanup(self.servers_client.delete_server, server['id'])
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        mountpoint = '/dev/%s' % CONF.compute.volume_device_name
        _, body = self.volumes_client.attach_volume(
            self.volume_origin['id'], server['id'], mountpoint)
        self.volumes_client.wait_for_volume_status(self.volume_origin['id'],
                                                   'in-use')
        self.addCleanup(self._detach, self.volume_origin['id'])
        # Snapshot a volume even if it's attached to an instance
        snapshot = self.create_snapshot(self.volume_origin['id'],
                                        force=True)
        # Delete the snapshot
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])
        self.snapshots.remove(snapshot)

    @test.attr(type='gate')
    def test_snapshot_create_get_list_update_delete(self):
        # Create a snapshot
        s_name = data_utils.rand_name('snap')
        snapshot = self.create_snapshot(self.volume_origin['id'],
                                        display_name=s_name)

        # Get the snap and check for some of its details
        _, snap_get = self.snapshots_client.get_snapshot(snapshot['id'])
        self.assertEqual(self.volume_origin['id'],
                         snap_get['volume_id'],
                         "Referred volume origin mismatch")

        # Compare also with the output from the list action
        tracking_data = (snapshot['id'], snapshot['display_name'])
        _, snaps_list = self.snapshots_client.list_snapshots()
        snaps_data = [(f['id'], f['display_name']) for f in snaps_list]
        self.assertIn(tracking_data, snaps_data)

        # Updates snapshot with new values
        new_s_name = data_utils.rand_name('new-snap')
        new_desc = 'This is the new description of snapshot.'
        _, update_snapshot = \
            self.snapshots_client.update_snapshot(snapshot['id'],
                                                  display_name=new_s_name,
                                                  display_description=new_desc)
        # Assert response body for update_snapshot method
        self.assertEqual(new_s_name, update_snapshot['display_name'])
        self.assertEqual(new_desc, update_snapshot['display_description'])
        # Assert response body for get_snapshot method
        _, updated_snapshot = \
            self.snapshots_client.get_snapshot(snapshot['id'])
        self.assertEqual(new_s_name, updated_snapshot['display_name'])
        self.assertEqual(new_desc, updated_snapshot['display_description'])

        # Delete the snapshot
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])
        self.snapshots.remove(snapshot)

    @test.attr(type='gate')
    def test_snapshots_list_with_params(self):
        """list snapshots with params."""
        # Create a snapshot
        display_name = data_utils.rand_name('snap')
        snapshot = self.create_snapshot(self.volume_origin['id'],
                                        display_name=display_name)

        # Verify list snapshots by display_name filter
        params = {'display_name': snapshot['display_name']}
        self._list_by_param_values_and_assert(params)

        # Verify list snapshots by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(params)

        # Verify list snapshots by status and display name filter
        params = {'status': 'available',
                  'display_name': snapshot['display_name']}
        self._list_by_param_values_and_assert(params)

    @test.attr(type='gate')
    def test_snapshots_list_details_with_params(self):
        """list snapshot details with params."""
        # Create a snapshot
        display_name = data_utils.rand_name('snap')
        snapshot = self.create_snapshot(self.volume_origin['id'],
                                        display_name=display_name)

        # Verify list snapshot details by display_name filter
        params = {'display_name': snapshot['display_name']}
        self._list_by_param_values_and_assert(params, with_detail=True)
        # Verify list snapshot details by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(params, with_detail=True)
        # Verify list snapshot details by status and display name filter
        params = {'status': 'available',
                  'display_name': snapshot['display_name']}
        self._list_by_param_values_and_assert(params, with_detail=True)

    @test.attr(type='gate')
    def test_volume_from_snapshot(self):
        # Create a temporary snap using wrapper method from base, then
        # create a snap based volume and deletes it
        snapshot = self.create_snapshot(self.volume_origin['id'])
        # NOTE(gfidente): size is required also when passing snapshot_id
        _, volume = self.volumes_client.create_volume(
            size=1,
            snapshot_id=snapshot['id'])
        self.volumes_client.wait_for_volume_status(volume['id'], 'available')
        self.volumes_client.delete_volume(volume['id'])
        self.volumes_client.wait_for_resource_deletion(volume['id'])
        self.clear_snapshots()


class VolumesSnapshotTestXML(VolumesSnapshotTest):
    _interface = "xml"
