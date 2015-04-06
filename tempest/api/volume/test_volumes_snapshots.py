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

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils

from tempest.api.volume import base
from tempest import config
from tempest import test

LOG = logging.getLogger(__name__)
CONF = config.CONF


class VolumesV2SnapshotTestJSON(base.BaseVolumeTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesV2SnapshotTestJSON, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    @classmethod
    def resource_setup(cls):
        super(VolumesV2SnapshotTestJSON, cls).resource_setup()
        cls.volume_origin = cls.create_volume()

        cls.name_field = cls.special_fields['name_field']
        cls.descrip_field = cls.special_fields['descrip_field']

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
            fetched_snap_list = \
                self.snapshots_client.\
                list_snapshots(detail=True, params=params)
        else:
            fetched_snap_list = \
                self.snapshots_client.list_snapshots(params=params)

        # Validating params of fetched snapshots
        for snap in fetched_snap_list:
            for key in params:
                msg = "Failed to list snapshots %s by %s" % \
                      ('details' if with_detail else '', key)
                self.assertEqual(params[key], snap[key], msg)

    @test.attr(type='gate')
    @test.idempotent_id('b467b54c-07a4-446d-a1cf-651dedcc3ff1')
    @test.services('compute')
    def test_snapshot_create_with_volume_in_use(self):
        # Create a snapshot when volume status is in-use
        # Create a test instance
        server_name = data_utils.rand_name('instance')
        server = self.create_server(server_name)
        self.addCleanup(self.servers_client.delete_server, server['id'])
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')
        mountpoint = '/dev/%s' % CONF.compute.volume_device_name
        self.servers_client.attach_volume(
            server['id'], self.volume_origin['id'], mountpoint)
        self.volumes_client.wait_for_volume_status(self.volume_origin['id'],
                                                   'in-use')
        self.addCleanup(self.volumes_client.wait_for_volume_status,
                        self.volume_origin['id'], 'available')
        self.addCleanup(self.servers_client.detach_volume, server['id'],
                        self.volume_origin['id'])
        # Snapshot a volume even if it's attached to an instance
        snapshot = self.create_snapshot(self.volume_origin['id'],
                                        force=True)
        # Delete the snapshot
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])
        self.snapshots.remove(snapshot)

    @test.attr(type='gate')
    @test.idempotent_id('2a8abbe4-d871-46db-b049-c41f5af8216e')
    def test_snapshot_create_get_list_update_delete(self):
        # Create a snapshot
        s_name = data_utils.rand_name('snap')
        params = {self.name_field: s_name}
        snapshot = self.create_snapshot(self.volume_origin['id'], **params)

        # Get the snap and check for some of its details
        snap_get = self.snapshots_client.show_snapshot(snapshot['id'])
        self.assertEqual(self.volume_origin['id'],
                         snap_get['volume_id'],
                         "Referred volume origin mismatch")

        # Compare also with the output from the list action
        tracking_data = (snapshot['id'], snapshot[self.name_field])
        snaps_list = self.snapshots_client.list_snapshots()
        snaps_data = [(f['id'], f[self.name_field]) for f in snaps_list]
        self.assertIn(tracking_data, snaps_data)

        # Updates snapshot with new values
        new_s_name = data_utils.rand_name('new-snap')
        new_desc = 'This is the new description of snapshot.'
        params = {self.name_field: new_s_name,
                  self.descrip_field: new_desc}
        update_snapshot = \
            self.snapshots_client.update_snapshot(snapshot['id'], **params)
        # Assert response body for update_snapshot method
        self.assertEqual(new_s_name, update_snapshot[self.name_field])
        self.assertEqual(new_desc, update_snapshot[self.descrip_field])
        # Assert response body for show_snapshot method
        updated_snapshot = \
            self.snapshots_client.show_snapshot(snapshot['id'])
        self.assertEqual(new_s_name, updated_snapshot[self.name_field])
        self.assertEqual(new_desc, updated_snapshot[self.descrip_field])

        # Delete the snapshot
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])
        self.snapshots.remove(snapshot)

    @test.attr(type='gate')
    @test.idempotent_id('59f41f43-aebf-48a9-ab5d-d76340fab32b')
    def test_snapshots_list_with_params(self):
        """list snapshots with params."""
        # Create a snapshot
        display_name = data_utils.rand_name('snap')
        params = {self.name_field: display_name}
        snapshot = self.create_snapshot(self.volume_origin['id'], **params)

        # Verify list snapshots by display_name filter
        params = {self.name_field: snapshot[self.name_field]}
        self._list_by_param_values_and_assert(params)

        # Verify list snapshots by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(params)

        # Verify list snapshots by status and display name filter
        params = {'status': 'available',
                  self.name_field: snapshot[self.name_field]}
        self._list_by_param_values_and_assert(params)

    @test.attr(type='gate')
    @test.idempotent_id('220a1022-1fcd-4a74-a7bd-6b859156cda2')
    def test_snapshots_list_details_with_params(self):
        """list snapshot details with params."""
        # Create a snapshot
        display_name = data_utils.rand_name('snap')
        params = {self.name_field: display_name}
        snapshot = self.create_snapshot(self.volume_origin['id'], **params)

        # Verify list snapshot details by display_name filter
        params = {self.name_field: snapshot[self.name_field]}
        self._list_by_param_values_and_assert(params, with_detail=True)
        # Verify list snapshot details by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(params, with_detail=True)
        # Verify list snapshot details by status and display name filter
        params = {'status': 'available',
                  self.name_field: snapshot[self.name_field]}
        self._list_by_param_values_and_assert(params, with_detail=True)

    @test.attr(type='gate')
    @test.idempotent_id('677863d1-3142-456d-b6ac-9924f667a7f4')
    def test_volume_from_snapshot(self):
        # Create a temporary snap using wrapper method from base, then
        # create a snap based volume and deletes it
        snapshot = self.create_snapshot(self.volume_origin['id'])
        # NOTE(gfidente): size is required also when passing snapshot_id
        volume = self.volumes_client.create_volume(
            snapshot_id=snapshot['id'])
        self.volumes_client.wait_for_volume_status(volume['id'], 'available')
        self.volumes_client.delete_volume(volume['id'])
        self.volumes_client.wait_for_resource_deletion(volume['id'])
        self.clear_snapshots()


class VolumesV1SnapshotTestJSON(VolumesV2SnapshotTestJSON):
    _api_version = 1
