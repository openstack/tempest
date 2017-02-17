# Copyright 2016 Red Hat, Inc.
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

from tempest.api.volume import base
from tempest import config
from tempest.lib import decorators

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
        cls.snapshot_id_list = []
        # Create a volume
        cls.volume_origin = cls.create_volume()
        # Create 3 snapshots
        for _ in range(3):
            snapshot = cls.create_snapshot(cls.volume_origin['id'])
            cls.snapshot_id_list.append(snapshot['id'])

    def _list_snapshots_param_sort(self, sort_key, sort_dir):
        """list snapshots by sort param"""
        snap_list = self.snapshots_client.list_snapshots(
            sort_key=sort_key, sort_dir=sort_dir)['snapshots']
        self.assertNotEmpty(snap_list)
        if sort_key is 'display_name':
            sort_key = 'name'
        # Note: On Cinder V2 API, 'display_name' works as a sort key
        # on a request, a volume name appears as 'name' on the response.
        # So Tempest needs to change the key name here for this inconsistent
        # API behavior.
        sorted_list = [snapshot[sort_key] for snapshot in snap_list]
        msg = 'The list of snapshots was not sorted correctly.'
        self.assertEqual(sorted(sorted_list, reverse=(sort_dir == 'desc')),
                         sorted_list, msg)

    @decorators.idempotent_id('c5513ada-64c1-4d28-83b9-af3307ec1388')
    def test_snapshot_list_param_sort_id_asc(self):
        self._list_snapshots_param_sort(sort_key='id', sort_dir='asc')

    @decorators.idempotent_id('8a7fe058-0b41-402a-8afd-2dbc5a4a718b')
    def test_snapshot_list_param_sort_id_desc(self):
        self._list_snapshots_param_sort(sort_key='id', sort_dir='desc')

    @decorators.idempotent_id('4052c3a0-2415-440a-a8cc-305a875331b0')
    def test_snapshot_list_param_sort_created_at_asc(self):
        self._list_snapshots_param_sort(sort_key='created_at', sort_dir='asc')

    @decorators.idempotent_id('dcbbe24a-f3c0-4ec8-9274-55d48db8d1cf')
    def test_snapshot_list_param_sort_created_at_desc(self):
        self._list_snapshots_param_sort(sort_key='created_at', sort_dir='desc')

    @decorators.idempotent_id('d58b5fed-0c37-42d3-8c5d-39014ac13c00')
    def test_snapshot_list_param_sort_name_asc(self):
        self._list_snapshots_param_sort(sort_key='display_name',
                                        sort_dir='asc')

    @decorators.idempotent_id('96ba6f4d-1f18-47e1-b4bc-76edc6c21250')
    def test_snapshot_list_param_sort_name_desc(self):
        self._list_snapshots_param_sort(sort_key='display_name',
                                        sort_dir='desc')

    @decorators.idempotent_id('05489dde-44bc-4961-a1f5-3ce7ee7824f7')
    def test_snapshot_list_param_marker(self):
        # The list of snapshots should end before the provided marker
        params = {'marker': self.snapshot_id_list[1]}
        snap_list = self.snapshots_client.list_snapshots(**params)['snapshots']
        fetched_list_id = [snap['id'] for snap in snap_list]
        # Verify the list of snapshots ends before the provided
        # marker(second snapshot), therefore only the first snapshot
        # should displayed.
        self.assertEqual(self.snapshot_id_list[:1], fetched_list_id)
