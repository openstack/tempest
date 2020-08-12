# Copyright 2015 Fujitsu(fnst) Corporation
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

from tempest.api.compute import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


CONF = config.CONF


class VolumesSnapshotsTestJSON(base.BaseV2ComputeTest):
    """Test volume snapshots with compute microversion less than 2.36"""

    # These tests will fail with a 404 starting from microversion 2.36. For
    # more information, see:
    # https://docs.openstack.org/api-ref/compute/#volume-extension-os-volumes-os-snapshots-deprecated
    max_microversion = '2.35'

    @classmethod
    def skip_checks(cls):
        super(VolumesSnapshotsTestJSON, cls).skip_checks()
        if not CONF.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if not CONF.volume_feature_enabled.snapshot:
            skip_msg = ("Cinder volume snapshots are disabled")
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(VolumesSnapshotsTestJSON, cls).setup_clients()
        cls.volumes_client = cls.volumes_extensions_client
        cls.snapshots_client = cls.snapshots_extensions_client

    @decorators.idempotent_id('cd4ec87d-7825-450d-8040-6e2068f2da8f')
    def test_volume_snapshot_create_get_list_delete(self):
        """Test create/get/list/delete volume snapshot"""
        volume = self.create_volume()
        self.addCleanup(self.delete_volume, volume['id'])

        s_name = data_utils.rand_name(self.__class__.__name__ + '-Snapshot')
        # Create snapshot
        snapshot = self.snapshots_client.create_snapshot(
            volume_id=volume['id'],
            display_name=s_name)['snapshot']

        def delete_snapshot(snapshot_id):
            waiters.wait_for_volume_resource_status(self.snapshots_client,
                                                    snapshot_id,
                                                    'available')
            # Delete snapshot
            self.snapshots_client.delete_snapshot(snapshot_id)
            self.snapshots_client.wait_for_resource_deletion(snapshot_id)

        self.addCleanup(delete_snapshot, snapshot['id'])
        self.assertEqual(volume['id'], snapshot['volumeId'])
        # Get snapshot
        fetched_snapshot = self.snapshots_client.show_snapshot(
            snapshot['id'])['snapshot']
        self.assertEqual(s_name, fetched_snapshot['displayName'])
        self.assertEqual(volume['id'], fetched_snapshot['volumeId'])
        # Fetch all snapshots
        snapshots = self.snapshots_client.list_snapshots()['snapshots']
        self.assertIn(snapshot['id'], map(lambda x: x['id'], snapshots))
