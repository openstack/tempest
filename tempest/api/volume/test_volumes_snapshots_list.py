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
from tempest import config
from tempest.lib import decorators
from tempest import test

CONF = config.CONF


class VolumesV2SnapshotListTestJSON(base.BaseVolumeTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesV2SnapshotListTestJSON, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    @classmethod
    def resource_setup(cls):
        super(VolumesV2SnapshotListTestJSON, cls).resource_setup()
        cls.volume_origin = cls.create_volume()
        cls.name_field = cls.special_fields['name_field']
        # Create snapshots with params
        for _ in range(2):
            cls.snapshot = cls.create_snapshot(cls.volume_origin['id'])

    def _list_by_param_values_and_assert(self, with_detail=False, **params):
        """list or list_details with given params and validates result."""

        fetched_snap_list = self.snapshots_client.list_snapshots(
            detail=with_detail, **params)['snapshots']

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

    @test.idempotent_id('59f41f43-aebf-48a9-ab5d-d76340fab32b')
    def test_snapshots_list_with_params(self):
        """list snapshots with params."""
        # Verify list snapshots by display_name filter
        params = {self.name_field: self.snapshot[self.name_field]}
        self._list_by_param_values_and_assert(**params)

        # Verify list snapshots by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(**params)

        # Verify list snapshots by status and display name filter
        params = {'status': 'available',
                  self.name_field: self.snapshot[self.name_field]}
        self._list_by_param_values_and_assert(**params)

    @test.idempotent_id('220a1022-1fcd-4a74-a7bd-6b859156cda2')
    def test_snapshots_list_details_with_params(self):
        """list snapshot details with params."""
        # Verify list snapshot details by display_name filter
        params = {self.name_field: self.snapshot[self.name_field]}
        self._list_by_param_values_and_assert(with_detail=True, **params)
        # Verify list snapshot details by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(with_detail=True, **params)
        # Verify list snapshot details by status and display name filter
        params = {'status': 'available',
                  self.name_field: self.snapshot[self.name_field]}
        self._list_by_param_values_and_assert(with_detail=True, **params)

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


class VolumesV1SnapshotLimitTestJSON(VolumesV2SnapshotListTestJSON):
    _api_version = 1
