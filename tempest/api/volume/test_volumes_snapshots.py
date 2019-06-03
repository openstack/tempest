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
from testtools import matchers

from tempest.api.volume import base
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class VolumesSnapshotTestJSON(base.BaseVolumeTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesSnapshotTestJSON, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    @classmethod
    def resource_setup(cls):
        super(VolumesSnapshotTestJSON, cls).resource_setup()
        cls.volume_origin = cls.create_volume()

    @decorators.idempotent_id('8567b54c-4455-446d-a1cf-651ddeaa3ff2')
    @utils.services('compute')
    def test_snapshot_create_delete_with_volume_in_use(self):
        # Create a test instance
        server = self.create_server()
        # NOTE(zhufl) Here we create volume from self.image_ref for adding
        # coverage for "creating snapshot from non-blank volume".
        volume = self.create_volume(imageRef=self.image_ref)
        self.attach_volume(server['id'], volume['id'])

        # Snapshot a volume which attached to an instance with force=False
        self.assertRaises(lib_exc.BadRequest, self.create_snapshot,
                          volume['id'], force=False)

        # Snapshot a volume attached to an instance
        snapshot1 = self.create_snapshot(volume['id'], force=True)
        snapshot2 = self.create_snapshot(volume['id'], force=True)
        snapshot3 = self.create_snapshot(volume['id'], force=True)

        # Delete the snapshots. Some snapshot implementations can take
        # different paths according to order they are deleted.
        self.delete_snapshot(snapshot1['id'])
        self.delete_snapshot(snapshot3['id'])
        self.delete_snapshot(snapshot2['id'])

    @decorators.idempotent_id('5210a1de-85a0-11e6-bb21-641c676a5d61')
    @utils.services('compute')
    def test_snapshot_create_offline_delete_online(self):

        # Create a snapshot while it is not attached
        snapshot1 = self.create_snapshot(self.volume_origin['id'])

        # Create a server and attach it
        server = self.create_server()
        self.attach_volume(server['id'], self.volume_origin['id'])

        # Now that the volume is attached, create another snapshots
        snapshot2 = self.create_snapshot(self.volume_origin['id'], force=True)
        snapshot3 = self.create_snapshot(self.volume_origin['id'], force=True)

        # Delete the snapshots. Some snapshot implementations can take
        # different paths according to order they are deleted.
        self.delete_snapshot(snapshot3['id'])
        self.delete_snapshot(snapshot1['id'])
        self.delete_snapshot(snapshot2['id'])

    @decorators.idempotent_id('2a8abbe4-d871-46db-b049-c41f5af8216e')
    def test_snapshot_create_get_list_update_delete(self):
        # Create a snapshot with metadata
        metadata = {"snap-meta1": "value1",
                    "snap-meta2": "value2",
                    "snap-meta3": "value3"}
        snapshot = self.create_snapshot(self.volume_origin['id'],
                                        metadata=metadata)

        # Get the snap and check for some of its details
        snap_get = self.snapshots_client.show_snapshot(
            snapshot['id'])['snapshot']
        self.assertEqual(self.volume_origin['id'],
                         snap_get['volume_id'],
                         "Referred volume origin mismatch")
        self.assertEqual(self.volume_origin['size'], snap_get['size'])

        # Verify snapshot metadata
        self.assertThat(snap_get['metadata'].items(),
                        matchers.ContainsAll(metadata.items()))

        # Compare also with the output from the list action
        tracking_data = (snapshot['id'], snapshot['name'])
        snaps_list = self.snapshots_client.list_snapshots()['snapshots']
        snaps_data = [(f['id'], f['name']) for f in snaps_list]
        self.assertIn(tracking_data, snaps_data)

        # Updates snapshot with new values
        new_s_name = data_utils.rand_name(
            self.__class__.__name__ + '-new-snap')
        new_desc = 'This is the new description of snapshot.'
        params = {'name': new_s_name,
                  'description': new_desc}
        update_snapshot = self.snapshots_client.update_snapshot(
            snapshot['id'], **params)['snapshot']
        # Assert response body for update_snapshot method
        self.assertEqual(new_s_name, update_snapshot['name'])
        self.assertEqual(new_desc, update_snapshot['description'])
        # Assert response body for show_snapshot method
        updated_snapshot = self.snapshots_client.show_snapshot(
            snapshot['id'])['snapshot']
        self.assertEqual(new_s_name, updated_snapshot['name'])
        self.assertEqual(new_desc, updated_snapshot['description'])

        # Delete the snapshot
        self.delete_snapshot(snapshot['id'])

    def _create_volume_from_snapshot(self, extra_size=0):
        src_size = CONF.volume.volume_size
        size = src_size + extra_size

        src_vol = self.create_volume(size=src_size)
        src_snap = self.create_snapshot(src_vol['id'])

        dst_vol = self.create_volume(snapshot_id=src_snap['id'],
                                     size=size)
        # NOTE(zhufl): dst_vol is created based on snapshot, so dst_vol
        # should be deleted before deleting snapshot, otherwise deleting
        # snapshot will end with status 'error-deleting'. This depends on
        # the implementation mechanism of vendors, generally speaking,
        # some verdors will use "virtual disk clone" which will promote
        # disk clone speed, and in this situation the "disk clone"
        # is just a relationship between volume and snapshot.
        self.addCleanup(self.delete_volume, self.volumes_client, dst_vol['id'])

        volume = self.volumes_client.show_volume(dst_vol['id'])['volume']
        # Should allow
        self.assertEqual(volume['snapshot_id'], src_snap['id'])
        self.assertEqual(volume['size'], size)

    @decorators.idempotent_id('677863d1-3142-456d-b6ac-9924f667a7f4')
    def test_volume_from_snapshot(self):
        # Creates a volume from a snapshot passing a size
        # different from the source
        self._create_volume_from_snapshot(extra_size=1)

    @decorators.idempotent_id('053d8870-8282-4fff-9dbb-99cb58bb5e0a')
    def test_volume_from_snapshot_no_size(self):
        # Creates a volume from a snapshot defaulting to original size
        self._create_volume_from_snapshot()

    @decorators.idempotent_id('bbcfa285-af7f-479e-8c1a-8c34fc16543c')
    @testtools.skipUnless(CONF.volume_feature_enabled.backup,
                          "Cinder backup is disabled")
    def test_snapshot_backup(self):
        # Create a snapshot
        snapshot = self.create_snapshot(volume_id=self.volume_origin['id'])

        backup = self.create_backup(volume_id=self.volume_origin['id'],
                                    snapshot_id=snapshot['id'])
        waiters.wait_for_volume_resource_status(self.snapshots_client,
                                                snapshot['id'], 'available')
        backup_info = self.backups_client.show_backup(backup['id'])['backup']
        self.assertEqual(self.volume_origin['id'], backup_info['volume_id'])
        self.assertEqual(snapshot['id'], backup_info['snapshot_id'])
