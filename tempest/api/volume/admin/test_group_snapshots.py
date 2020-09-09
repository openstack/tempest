# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
# Copyright (C) 2017 Dell Inc. or its subsidiaries.
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
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators

CONF = config.CONF


class BaseGroupSnapshotsTest(base.BaseVolumeAdminTest):

    @classmethod
    def skip_checks(cls):
        super(BaseGroupSnapshotsTest, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    def _create_group_snapshot(self, **kwargs):
        if 'name' not in kwargs:
            kwargs['name'] = data_utils.rand_name(
                self.__class__.__name__ + '-Group_Snapshot')

        group_snapshot = self.group_snapshots_client.create_group_snapshot(
            **kwargs)['group_snapshot']
        group_snapshot['group_id'] = kwargs['group_id']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self._delete_group_snapshot, group_snapshot)
        waiters.wait_for_volume_resource_status(
            self.group_snapshots_client, group_snapshot['id'], 'available')
        return group_snapshot

    def _delete_group_snapshot(self, group_snapshot):
        self.group_snapshots_client.delete_group_snapshot(group_snapshot['id'])
        vols = self.volumes_client.list_volumes(detail=True)['volumes']
        snapshots = self.snapshots_client.list_snapshots(
            detail=True)['snapshots']
        for vol in vols:
            for snap in snapshots:
                if (vol['group_id'] == group_snapshot['group_id'] and
                        vol['id'] == snap['volume_id']):
                    self.snapshots_client.wait_for_resource_deletion(
                        snap['id'])
        self.group_snapshots_client.wait_for_resource_deletion(
            group_snapshot['id'])


class GroupSnapshotsTest(BaseGroupSnapshotsTest):
    """Test group snapshot"""

    _api_version = 3
    min_microversion = '3.14'
    max_microversion = 'latest'

    @decorators.idempotent_id('1298e537-f1f0-47a3-a1dd-8adec8168897')
    def test_group_snapshot_create_show_list_delete(self):
        """Test create/show/list/delete group snapshot

        1. Create volume type "volume_type1"
        2. Create group type "group_type1"
        3. Create group "group1" with "group_type1" and "volume_type1"
        4. Create volume "volume1" with "volume_type1" and "group1"
        5. Create group snapshot "group_snapshot1" with "group1"
        6. Check snapshot created from "volume1" reaches available status
        7. Check the created group snapshot "group_snapshot1" is in the list
           of all group snapshots
        8. Delete group snapshot "group_snapshot1"
        """
        # Create volume type
        volume_type = self.create_volume_type()

        # Create group type
        group_type = self.create_group_type()

        # Create group
        grp = self.create_group(group_type=group_type['id'],
                                volume_types=[volume_type['id']])

        # Create volume
        vol = self.create_volume(volume_type=volume_type['id'],
                                 group_id=grp['id'])

        # Create group snapshot
        group_snapshot_name = data_utils.rand_name('group_snapshot')
        group_snapshot = self._create_group_snapshot(
            group_id=grp['id'], name=group_snapshot_name)
        snapshots = self.snapshots_client.list_snapshots(
            detail=True)['snapshots']
        for snap in snapshots:
            if vol['id'] == snap['volume_id']:
                waiters.wait_for_volume_resource_status(
                    self.snapshots_client, snap['id'], 'available')
        self.assertEqual(group_snapshot_name, group_snapshot['name'])

        # Get a given group snapshot
        group_snapshot = self.group_snapshots_client.show_group_snapshot(
            group_snapshot['id'])['group_snapshot']
        self.assertEqual(group_snapshot_name, group_snapshot['name'])

        # Get all group snapshots with details, check some detail-specific
        # elements, and look for the created group snapshot
        group_snapshots = self.group_snapshots_client.list_group_snapshots(
            detail=True)['group_snapshots']
        for grp_snapshot in group_snapshots:
            self.assertIn('created_at', grp_snapshot)
            self.assertIn('group_id', grp_snapshot)
        self.assertIn((group_snapshot['name'], group_snapshot['id']),
                      [(m['name'], m['id']) for m in group_snapshots])

        # Delete group snapshot
        self._delete_group_snapshot(group_snapshot)
        group_snapshots = self.group_snapshots_client.list_group_snapshots()[
            'group_snapshots']
        self.assertNotIn((group_snapshot['name'], group_snapshot['id']),
                         [(m['name'], m['id']) for m in group_snapshots])

    @decorators.idempotent_id('eff52c70-efc7-45ed-b47a-4ad675d09b81')
    def test_create_group_from_group_snapshot(self):
        """Test creating group from group snapshot

        1. Create volume type "volume_type1"
        2. Create group type "group_type1"
        3. Create group "group1" with "group_type1" and "volume_type1"
        4. Create volume "volume1" with "volume_type1" and "group1"
        5. Create group snapshot "group_snapshot1" with "group1"
        6. Check snapshot created from "volume1" reaches available status
        7. Create group "group2" from "group_snapshot1"
        8. Check the volumes belonging to "group2" reach available status
        9. Check "group2" reaches available status
        """
        # Create volume type
        volume_type = self.create_volume_type()

        # Create group type
        group_type = self.create_group_type()

        # Create Group
        grp = self.create_group(group_type=group_type['id'],
                                volume_types=[volume_type['id']])

        # Create volume
        vol = self.create_volume(volume_type=volume_type['id'],
                                 group_id=grp['id'])

        # Create group_snapshot
        group_snapshot_name = data_utils.rand_name('group_snapshot')
        group_snapshot = self._create_group_snapshot(
            group_id=grp['id'], name=group_snapshot_name)
        self.assertEqual(group_snapshot_name, group_snapshot['name'])
        snapshots = self.snapshots_client.list_snapshots(
            detail=True)['snapshots']
        for snap in snapshots:
            if vol['id'] == snap['volume_id']:
                waiters.wait_for_volume_resource_status(
                    self.snapshots_client, snap['id'], 'available')

        # Create Group from Group snapshot
        grp_name2 = data_utils.rand_name('Group_from_snap')
        grp2 = self.groups_client.create_group_from_source(
            group_snapshot_id=group_snapshot['id'], name=grp_name2)['group']
        self.addCleanup(self.delete_group, grp2['id'])
        self.assertEqual(grp_name2, grp2['name'])
        vols = self.volumes_client.list_volumes(detail=True)['volumes']
        for vol in vols:
            if vol['group_id'] == grp2['id']:
                waiters.wait_for_volume_resource_status(
                    self.volumes_client, vol['id'], 'available')
        waiters.wait_for_volume_resource_status(
            self.groups_client, grp2['id'], 'available')

    @decorators.idempotent_id('7d7fc000-0b4c-4376-a372-544116d2e127')
    @decorators.related_bug('1739031')
    def test_delete_group_snapshots_following_updated_volumes(self):
        """Test deleting group snapshot following updated volumes

        1. Create volume type "volume_type1"
        2. Create group type "group_type1"
        3. Create group "group1" with "group_type1" and "volume_type1"
        4. Create 2 volumes "volume1" and "volume2"
           with "volume_type1" and "group1"
        5. For each created volume, removing and then adding back to "group1"
        6. Create group snapshot "group_snapshot1" with "group1"
        7. Check snapshots created from "volume1" and "volume2" reach
           available status
        8. Delete "group_snapshot1"
        9. Check snapshots created from "volume1" and "volume2" are deleted
        """
        volume_type = self.create_volume_type()

        group_type = self.create_group_type()

        # Create a volume group
        grp = self.create_group(group_type=group_type['id'],
                                volume_types=[volume_type['id']])

        # Note: When dealing with consistency groups all volumes must
        # reside on the same backend. Adding volumes to the same consistency
        # group from multiple backends isn't supported. In order to ensure all
        # volumes share the same backend, all volumes must share same
        # volume-type and group id.
        volume_list = []
        for _ in range(2):
            volume = self.create_volume(volume_type=volume_type['id'],
                                        group_id=grp['id'])
            volume_list.append(volume['id'])

        for vol in volume_list:
            self.groups_client.update_group(grp['id'],
                                            remove_volumes=vol)
            waiters.wait_for_volume_resource_status(
                self.groups_client, grp['id'], 'available')

            self.groups_client.update_group(grp['id'],
                                            add_volumes=vol)
            waiters.wait_for_volume_resource_status(
                self.groups_client, grp['id'], 'available')

        # Verify the created volumes are associated with consistency group
        vols = self.volumes_client.list_volumes(detail=True)['volumes']
        grp_vols = [v for v in vols if v['group_id'] == grp['id']]
        self.assertEqual(2, len(grp_vols))

        # Create a snapshot group
        group_snapshot = self._create_group_snapshot(group_id=grp['id'])
        snapshots = self.snapshots_client.list_snapshots(
            detail=True)['snapshots']

        for snap in snapshots:
            if snap['volume_id'] in volume_list:
                waiters.wait_for_volume_resource_status(
                    self.snapshots_client, snap['id'], 'available')

        # Delete a snapshot group
        self._delete_group_snapshot(group_snapshot)


class GroupSnapshotsV319Test(BaseGroupSnapshotsTest):
    """Test group snapshot with volume microversion greater than 3.18"""

    _api_version = 3
    min_microversion = '3.19'
    max_microversion = 'latest'

    @decorators.idempotent_id('3b42c9b9-c984-4444-816e-ca2e1ed30b40')
    @decorators.skip_because(bug='1770179')
    def test_reset_group_snapshot_status(self):
        """Test resetting group snapshot status to creating/available/error"""
        # Create volume type
        volume_type = self.create_volume_type()

        # Create group type
        group_type = self.create_group_type()

        # Create group
        group = self.create_group(group_type=group_type['id'],
                                  volume_types=[volume_type['id']])

        # Create volume
        volume = self.create_volume(volume_type=volume_type['id'],
                                    group_id=group['id'])

        # Create group snapshot
        group_snapshot = self._create_group_snapshot(group_id=group['id'])
        snapshots = self.snapshots_client.list_snapshots(
            detail=True)['snapshots']
        for snap in snapshots:
            if volume['id'] == snap['volume_id']:
                waiters.wait_for_volume_resource_status(
                    self.snapshots_client, snap['id'], 'available')

        # Reset group snapshot status
        self.addCleanup(waiters.wait_for_volume_resource_status,
                        self.group_snapshots_client,
                        group_snapshot['id'], 'available')
        self.addCleanup(
            self.admin_group_snapshots_client.reset_group_snapshot_status,
            group_snapshot['id'], 'available')
        for status in ['creating', 'available', 'error']:
            self.admin_group_snapshots_client.reset_group_snapshot_status(
                group_snapshot['id'], status)
            waiters.wait_for_volume_resource_status(
                self.group_snapshots_client, group_snapshot['id'], status)
