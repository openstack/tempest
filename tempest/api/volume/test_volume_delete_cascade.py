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

import operator

import testtools

from tempest.api.volume import base
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class VolumesDeleteCascade(base.BaseVolumeTest):
    """Delete a volume with associated snapshots.

    Cinder provides the ability to delete a volume with its
    associated snapshots.
    It is allow a volume and its snapshots to be removed in one operation
    both for usability and performance reasons.
    """

    @classmethod
    def skip_checks(cls):
        super(VolumesDeleteCascade, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder snapshot feature disabled")

    def _assert_cascade_delete(self, volume_id):
        # Fetch volume ids
        volume_list = [
            vol['id'] for vol in
            self.volumes_client.list_volumes()['volumes']
            ]

        # Verify the parent volume was deleted
        self.assertNotIn(volume_id, volume_list)

        # List snapshots
        snapshot_list = self.snapshots_client.list_snapshots()['snapshots']

        # Verify snapshots were deleted
        self.assertNotIn(volume_id, map(operator.itemgetter('volume_id'),
                                        snapshot_list))

    @decorators.idempotent_id('994e2d40-de37-46e8-b328-a58fba7e4a95')
    def test_volume_delete_cascade(self):
        """Test deleting a volume with associated snapshots

        The case validates the ability to delete a volume
        with associated snapshots.
        """

        # Create a volume
        volume = self.create_volume()

        for _ in range(2):
            self.create_snapshot(volume['id'])

        # Delete the parent volume with associated snapshots
        self.volumes_client.delete_volume(volume['id'], cascade=True)
        self.volumes_client.wait_for_resource_deletion(volume['id'])

        # Verify volume parent was deleted with its associated snapshots
        self._assert_cascade_delete(volume['id'])

    @decorators.idempotent_id('59a77ede-609b-4ee8-9f68-fc3c6ffe97b5')
    @testtools.skipIf(CONF.volume.storage_protocol == 'ceph',
                      'Skip because of Bug#1677525')
    def test_volume_from_snapshot_cascade_delete(self):
        """Test deleting a volume with associated volume-associated snapshot

        The case validates the ability to delete a volume with
        associated snapshot while there is another volume created
        from that snapshot.
        """

        # Create a volume
        volume = self.create_volume()

        snapshot = self.create_snapshot(volume['id'])

        # Create volume from snapshot
        volume_snap = self.create_volume(snapshot_id=snapshot['id'])
        volume_details = self.volumes_client.show_volume(
            volume_snap['id'])['volume']
        self.assertEqual(snapshot['id'], volume_details['snapshot_id'])

        # Delete the parent volume with associated snapshot
        self.volumes_client.delete_volume(volume['id'], cascade=True)
        self.volumes_client.wait_for_resource_deletion(volume['id'])

        # Verify volume parent was deleted with its associated snapshot
        self._assert_cascade_delete(volume['id'])
