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

CONF = config.CONF


class VolumesSnapshotListTestJSON(base.BaseVolumeTest):
    """Test listing volume snapshots"""

    @classmethod
    def skip_checks(cls):
        super(VolumesSnapshotListTestJSON, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    @classmethod
    def resource_setup(cls):
        super(VolumesSnapshotListTestJSON, cls).resource_setup()
        volume_origin = cls.create_volume()

        # Create snapshots with params
        for _ in range(3):
            snapshot = cls.create_snapshot(volume_origin['id'])
        cls.snapshot = snapshot

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

    @decorators.idempotent_id('59f41f43-aebf-48a9-ab5d-d76340fab32b')
    def test_snapshots_list_with_params(self):
        """Test listing snapshots with params"""

        # Verify list snapshots by display_name filter
        params = {'name': self.snapshot['name']}
        self._list_by_param_values_and_assert(**params)

        # Verify list snapshots by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(**params)

        # Verify list snapshots by status and display name filter
        params = {'status': 'available',
                  'name': self.snapshot['name']}
        self._list_by_param_values_and_assert(**params)

    @decorators.idempotent_id('220a1022-1fcd-4a74-a7bd-6b859156cda2')
    def test_snapshots_list_details_with_params(self):
        """Test listing snapshot details with params"""

        # Verify list snapshot details by display_name filter
        params = {'name': self.snapshot['name']}
        self._list_by_param_values_and_assert(with_detail=True, **params)
        # Verify list snapshot details by status filter
        params = {'status': 'available'}
        self._list_by_param_values_and_assert(with_detail=True, **params)
        # Verify list snapshot details by status and display name filter
        params = {'status': 'available',
                  'name': self.snapshot['name']}
        self._list_by_param_values_and_assert(with_detail=True, **params)

    @decorators.idempotent_id('db4d8e0a-7a2e-41cc-a712-961f6844e896')
    def test_snapshot_list_param_limit(self):
        """Test listing snapshot with limit returns the limited elements

        If listing snapshots with limit=1, then 1 snapshot is returned.
        """
        self._list_snapshots_by_param_limit(limit=1, expected_elements=1)

    @decorators.idempotent_id('a1427f61-420e-48a5-b6e3-0b394fa95400')
    def test_snapshot_list_param_limit_equals_infinite(self):
        """Test listing snapshot with infinite limit

        If listing snapshots with limit greater than the count of all
        snapshots, then all snapshots are returned.
        """
        snap_list = self.snapshots_client.list_snapshots()['snapshots']
        self._list_snapshots_by_param_limit(limit=100000,
                                            expected_elements=len(snap_list))

    @decorators.idempotent_id('e3b44b7f-ae87-45b5-8a8c-66110eb24d0a')
    def test_snapshot_list_param_limit_equals_zero(self):
        """Test listing snapshot with zero limit should return empty list"""
        self._list_snapshots_by_param_limit(limit=0, expected_elements=0)

    def _list_snapshots_param_sort(self, sort_key, sort_dir):
        snap_list = self.snapshots_client.list_snapshots(
            sort_key=sort_key, sort_dir=sort_dir)['snapshots']
        self.assertNotEmpty(snap_list)
        if sort_key == 'display_name':
            sort_key = 'name'
        # Note: On Cinder API, 'display_name' works as a sort key
        # on a request, a volume name appears as 'name' on the response.
        # So Tempest needs to change the key name here for this inconsistent
        # API behavior.
        sorted_list = [snapshot[sort_key] for snapshot in snap_list]
        msg = 'The list of snapshots was not sorted correctly.'
        self.assertEqual(sorted(sorted_list, reverse=(sort_dir == 'desc')),
                         sorted_list, msg)

    @decorators.idempotent_id('c5513ada-64c1-4d28-83b9-af3307ec1388')
    def test_snapshot_list_param_sort_id_asc(self):
        """Test listing snapshots sort by id ascendingly"""
        self._list_snapshots_param_sort(sort_key='id', sort_dir='asc')

    @decorators.idempotent_id('8a7fe058-0b41-402a-8afd-2dbc5a4a718b')
    def test_snapshot_list_param_sort_id_desc(self):
        """Test listing snapshots sort by id descendingly"""
        self._list_snapshots_param_sort(sort_key='id', sort_dir='desc')

    @decorators.idempotent_id('4052c3a0-2415-440a-a8cc-305a875331b0')
    def test_snapshot_list_param_sort_created_at_asc(self):
        """Test listing snapshots sort by created_at ascendingly"""
        self._list_snapshots_param_sort(sort_key='created_at', sort_dir='asc')

    @decorators.idempotent_id('dcbbe24a-f3c0-4ec8-9274-55d48db8d1cf')
    def test_snapshot_list_param_sort_created_at_desc(self):
        """Test listing snapshots sort by created_at descendingly"""
        self._list_snapshots_param_sort(sort_key='created_at', sort_dir='desc')

    @decorators.idempotent_id('d58b5fed-0c37-42d3-8c5d-39014ac13c00')
    def test_snapshot_list_param_sort_name_asc(self):
        """Test listing snapshots sort by display_name ascendingly"""
        self._list_snapshots_param_sort(sort_key='display_name',
                                        sort_dir='asc')

    @decorators.idempotent_id('96ba6f4d-1f18-47e1-b4bc-76edc6c21250')
    def test_snapshot_list_param_sort_name_desc(self):
        """Test listing snapshots sort by display_name descendingly"""
        self._list_snapshots_param_sort(sort_key='display_name',
                                        sort_dir='desc')

    @decorators.idempotent_id('05489dde-44bc-4961-a1f5-3ce7ee7824f7')
    def test_snapshot_list_param_marker(self):
        """Test listing snapshots with marker

        The list of snapshots should end before the provided marker
        """
        snap_list = self.snapshots_client.list_snapshots()['snapshots']
        # list_snapshots will take the reverse order as they are created.
        snapshot_id_list = [snap['id'] for snap in snap_list][::-1]

        params = {'marker': snapshot_id_list[1]}
        snap_list = self.snapshots_client.list_snapshots(**params)['snapshots']
        fetched_list_id = [snap['id'] for snap in snap_list]
        # Verify the list of snapshots ends before the provided
        # marker(second snapshot), therefore only the first snapshot
        # should displayed.
        self.assertEqual(snapshot_id_list[:1], fetched_list_id)

    @decorators.idempotent_id('ca96d551-17c6-4e11-b0e8-52d3bb8a63c7')
    def test_snapshot_list_param_offset(self):
        """Test listing snapshots with offset and limit

        If listing snapshots with offset=2 and limit=3, then at most 3(limit)
        snapshots located in the position 2(offset) in the all snapshots list
        should be returned.
        (The items in the all snapshots list start from position 0.)
        """
        params = {'offset': 2, 'limit': 3}
        snap_list = self.snapshots_client.list_snapshots(**params)['snapshots']
        # Verify the list of snapshots skip offset=2 from the first element
        # (total 3 elements), therefore only one snapshot should display
        self.assertEqual(1, len(snap_list))
