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

import testtools

from tempest.api.volume import base
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class SnapshotManageAdminV2Test(base.BaseVolumeAdminTest):
    """Unmanage & manage snapshots

     This feature provides the ability to import/export volume snapshot
     from one Cinder to another and to import snapshots that have not been
     managed by Cinder from a storage back end to Cinder
    """

    @decorators.idempotent_id('0132f42d-0147-4b45-8501-cc504bbf7810')
    @testtools.skipUnless(CONF.volume_feature_enabled.manage_snapshot,
                          "Manage snapshot tests are disabled")
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

        # Fetch snapshot ids
        snapshot_list = [
            snap['id'] for snap in
            self.snapshots_client.list_snapshots()['snapshots']
        ]

        # Verify snapshot does not exist in snapshot list
        self.assertNotIn(snapshot['id'], snapshot_list)

        # Manage the snapshot
        snapshot_ref = '_snapshot-%s' % snapshot['id']
        new_snapshot = self.admin_snapshot_manage_client.manage_snapshot(
            volume_id=volume['id'],
            ref={'source-name': snapshot_ref})['snapshot']
        self.addCleanup(self.delete_snapshot,
                        self.admin_snapshots_client, new_snapshot['id'])

        # Wait for the snapshot to be available after manage operation
        waiters.wait_for_snapshot_status(self.admin_snapshots_client,
                                         new_snapshot['id'],
                                         'available')

        # Verify the managed snapshot has the expected parent volume
        self.assertEqual(new_snapshot['volume_id'], volume['id'])
