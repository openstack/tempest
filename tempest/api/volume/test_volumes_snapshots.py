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
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest import test

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
        # Create 2 snapshots
        for _ in range(2):
            cls.create_snapshot(cls.volume_origin['id'])

    def _detach(self, volume_id):
        """Detach volume."""
        self.volumes_client.detach_volume(volume_id)
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume_id, 'available')

    def _list_by_param_values_and_assert(self, with_detail=False, **params):
        """list or list_details with given params and validates result."""

        if with_detail:
            fetched_snap_list = self.snapshots_client.list_snapshots(
                detail=True, **params)['snapshots']
        else:
            fetched_snap_list = self.snapshots_client.list_snapshots(
                **params)['snapshots']

        # Validating params of fetched snapshots
        for snap in fetched_snap_list:
            for key in params:
                msg = "Failed to list snapshots %s by %s" % \
                      ('details' if with_detail else '', key)
                self.assertEqual(params[key], snap[key], msg)

    def _list_snapshots_by_param_limit(self, limit, expected_elements):
        """list snapshots by limit param"""
        # Get snapshots list using limit parameter
        fetched_snap_list = self.snapshots_client.list_snapshots(
            limit=limit)['snapshots']
        # Validating filtered snapshots length equals to expected_elements
        self.assertEqual(expected_elements, len(fetched_snap_list))

    @test.idempotent_id('b467b54c-07a4-446d-a1cf-651dedcc3ff1')
    @test.services('compute')
    def test_snapshot_create_with_volume_in_use(self):
        # Create a snapshot when volume status is in-use
        # Create a test instance
        server_name = data_utils.rand_name(
            self.__class__.__name__ + '-instance')
        server = self.create_server(
            name=server_name,
            wait_until='ACTIVE')
        self.servers_client.attach_volume(
            server['id'], volumeId=self.volume_origin['id'],
            device='/dev/%s' % CONF.compute.volume_device_name)
        waiters.wait_for_volume_status(self.volumes_client,
                                       self.volume_origin['id'], 'in-use')
        self.addCleanup(waiters.wait_for_volume_status, self.volumes_client,
                        self.volume_origin['id'], 'available')
        self.addCleanup(self.servers_client.detach_volume, server['id'],
                        self.volume_origin['id'])
        # Snapshot a volume even if it's attached to an instance
        snapshot = self.create_snapshot(self.volume_origin['id'],
                                        force=True)
        # Delete the snapshot
        self.cleanup_snapshot(snapshot)

    @test.idempotent_id('2a8abbe4-d871-46db-b049-c41f5af8216e')
    def test_snapshot_create_get_list_update_delete(self):
        # Create a snapshot
        s_name = data_utils.rand_name(self.__class__.__name__ + '-snap')
        params = {self.name_field: s_name}
        snapshot = self.create_snapshot(self.volume_origin['id'], **params)

        # Get the snap and check for some of its details
        snap_get = self.snapshots_client.show_snapshot(
            snapshot['id'])['snapshot']
        self.assertEqual(self.volume_origin['id'],
                         snap_get['volume_id'],
                         "Referred volume origin mismatch")

        # Compare also with the output from the list action
        tracking_data = (snapshot['id'], snapshot[self.name_field])
        snaps_list = self.snapshots_client.list_snapshots()['snapshots']
        snaps_data = [(f['id'], f[self.name_field]) for f in snaps_list]
        self.assertIn(tracking_data, snaps_data)

        # Updates snapshot with new values
        new_s_name = data_utils.rand_name(
            self.__class__.__name__ + '-new-snap')
        new_desc = 'This is the new description of snapshot.'
        params = {self.name_field: new_s_name,
                  self.descrip_field: new_desc}
        update_snapshot = self.snapshots_client.update_snapshot(
            snapshot['id'], **params)['snapshot']
        # Assert response body for update_snapshot method
        self.assertEqual(new_s_name, update_snapshot[self.name_field])
        self.assertEqual(new_desc, update_snapshot[self.descrip_field])
        # Assert response body for show_snapshot method
        updated_snapshot = self.snapshots_client.show_snapshot(
            snapshot['id'])['snapshot']
        self.assertEqual(new_s_name, updated_snapshot[self.name_field])
        self.assertEqual(new_desc, updated_snapshot[self.descrip_field])

        # Delete the snapshot
        self.cleanup_snapshot(snapshot)

    @test.idempotent_id('59f41f43-aebf-48a9-ab5d-d76340fab32b')
    def test_snapshots_list_with_params(self):
        """list snapshots with params."""
        # Create a snapshot
        display_name = data_utils.rand_name(self.__class__.__name__ + '-snap')
        params = {self.name_field: display_name}
        snapshot = self.create_snapshot(self.volume_origin['id'], **params)
        self.addCleanup(self.cleanup_snapshot, snapshot)

        # Verify list snapshots by display_name filter
        params = {self.name_field: snapshot[self.name_field]}
        self._list_by_param_values_and_assert(**params)

        # Verify list snapshots by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(**params)

        # Verify list snapshots by status and display name filter
        params = {'status': 'available',
                  self.name_field: snapshot[self.name_field]}
        self._list_by_param_values_and_assert(**params)

    @test.idempotent_id('220a1022-1fcd-4a74-a7bd-6b859156cda2')
    def test_snapshots_list_details_with_params(self):
        """list snapshot details with params."""
        # Create a snapshot
        display_name = data_utils.rand_name(self.__class__.__name__ + '-snap')
        params = {self.name_field: display_name}
        snapshot = self.create_snapshot(self.volume_origin['id'], **params)
        self.addCleanup(self.cleanup_snapshot, snapshot)

        # Verify list snapshot details by display_name filter
        params = {self.name_field: snapshot[self.name_field]}
        self._list_by_param_values_and_assert(with_detail=True, **params)
        # Verify list snapshot details by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(with_detail=True, **params)
        # Verify list snapshot details by status and display name filter
        params = {'status': 'available',
                  self.name_field: snapshot[self.name_field]}
        self._list_by_param_values_and_assert(with_detail=True, **params)

    @test.idempotent_id('677863d1-3142-456d-b6ac-9924f667a7f4')
    def test_volume_from_snapshot(self):
        # Creates a volume a snapshot passing a size different from the source
        src_size = CONF.volume.volume_size

        src_vol = self.create_volume(size=src_size)
        src_snap = self.create_snapshot(src_vol['id'])
        # Destination volume bigger than source snapshot
        dst_vol = self.create_volume(snapshot_id=src_snap['id'],
                                     size=src_size + 1)

        volume = self.volumes_client.show_volume(dst_vol['id'])['volume']
        # Should allow
        self.assertEqual(volume['snapshot_id'], src_snap['id'])
        self.assertEqual(int(volume['size']), src_size + 1)

    @test.idempotent_id('db4d8e0a-7a2e-41cc-a712-961f6844e896')
    def test_snapshot_list_param_limit(self):
        # List returns limited elements
        self._list_snapshots_by_param_limit(limit=1, expected_elements=1)

    @test.idempotent_id('a1427f61-420e-48a5-b6e3-0b394fa95400')
    def test_snapshot_list_param_limit_equals_infinite(self):
        # List returns all elements when request limit exceeded
        # snapshots number
        snap_list = self.snapshots_client.list_snapshots()['snapshots']
        self._list_snapshots_by_param_limit(limit=100000,
                                            expected_elements=len(snap_list))

    @decorators.skip_because(bug='1540893')
    @test.idempotent_id('e3b44b7f-ae87-45b5-8a8c-66110eb24d0a')
    def test_snapshot_list_param_limit_equals_zero(self):
        # List returns zero elements
        self._list_snapshots_by_param_limit(limit=0, expected_elements=0)

    def cleanup_snapshot(self, snapshot):
        # Delete the snapshot
        self.snapshots_client.delete_snapshot(snapshot['id'])
        self.snapshots_client.wait_for_resource_deletion(snapshot['id'])
        self.snapshots.remove(snapshot)


class VolumesV1SnapshotTestJSON(VolumesV2SnapshotTestJSON):
    _api_version = 1
