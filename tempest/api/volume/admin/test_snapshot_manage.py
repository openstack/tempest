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
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions

CONF = config.CONF


class SnapshotManageAdminTest(base.BaseVolumeAdminTest):
    """Unmanage & manage snapshots

     This feature provides the ability to import/export volume snapshot
     from one Cinder to another and to import snapshots that have not been
     managed by Cinder from a storage back end to Cinder
    """

    @classmethod
    def skip_checks(cls):
        super(SnapshotManageAdminTest, cls).skip_checks()

        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

        if not CONF.volume_feature_enabled.manage_snapshot:
            raise cls.skipException("Manage snapshot tests are disabled")

        if len(CONF.volume.manage_snapshot_ref) != 2:
            msg = ("Manage snapshot ref is not correctly configured, "
                   "it should be a list of two elements")
            raise exceptions.InvalidConfiguration(msg)

    @decorators.idempotent_id('0132f42d-0147-4b45-8501-cc504bbf7810')
    def test_unmanage_manage_snapshot(self):
        # Create a volume
        volume = self.create_volume()

        # Create a snapshot
        snapshot = self.create_snapshot(volume_id=volume['id'])

        # Unmanage the snapshot
        # Unmanage snapshot function works almost the same as delete snapshot,
        # but it does not delete the snapshot data
        self.admin_snapshots_client.unmanage_snapshot(snapshot['id'])
        self.admin_snapshots_client.wait_for_resource_deletion(snapshot['id'])

        # Verify the original snapshot does not exist in snapshot list
        params = {'all_tenants': 1}
        all_snapshots = self.admin_snapshots_client.list_snapshots(
            detail=True, **params)['snapshots']
        self.assertNotIn(snapshot['id'], [v['id'] for v in all_snapshots])

        # Manage the snapshot
        name = data_utils.rand_name(self.__class__.__name__ +
                                    '-Managed-Snapshot')
        description = data_utils.rand_name(self.__class__.__name__ +
                                           '-Managed-Snapshot-Description')
        metadata = {"manage-snap-meta1": "value1",
                    "manage-snap-meta2": "value2",
                    "manage-snap-meta3": "value3"}
        snapshot_ref = {
            'volume_id': volume['id'],
            'ref': {CONF.volume.manage_snapshot_ref[0]:
                    CONF.volume.manage_snapshot_ref[1] % snapshot['id']},
            'name': name,
            'description': description,
            'metadata': metadata
        }
        new_snapshot = self.admin_snapshot_manage_client.manage_snapshot(
            **snapshot_ref)['snapshot']
        self.addCleanup(self.delete_snapshot, new_snapshot['id'],
                        self.admin_snapshots_client)

        # Wait for the snapshot to be available after manage operation
        waiters.wait_for_volume_resource_status(self.admin_snapshots_client,
                                                new_snapshot['id'],
                                                'available')

        # Verify the managed snapshot has the expected parent volume
        # and the expected field values.
        new_snapshot_info = self.admin_snapshots_client.show_snapshot(
            new_snapshot['id'])['snapshot']
        self.assertEqual(snapshot['size'], new_snapshot_info['size'])
        for key in ['volume_id', 'name', 'description', 'metadata']:
            self.assertEqual(snapshot_ref[key], new_snapshot_info[key])
