# Copyright 2013 Huawei Technologies Co.,LTD
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
from tempest.lib import decorators

CONF = config.CONF


class SnapshotsActionsTest(base.BaseVolumeAdminTest):
    """Test volume snapshot actions"""

    @classmethod
    def skip_checks(cls):
        super(SnapshotsActionsTest, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder snapshot feature disabled")

    @classmethod
    def resource_setup(cls):
        super(SnapshotsActionsTest, cls).resource_setup()

        # Create a test shared volume for tests
        cls.volume = cls.create_volume()

        # Create a test shared snapshot for tests
        cls.snapshot = cls.create_snapshot(volume_id=cls.volume['id'])

    def tearDown(self):
        # Set snapshot's status to available after test
        status = 'available'
        snapshot_id = self.snapshot['id']
        self.admin_snapshots_client.reset_snapshot_status(snapshot_id,
                                                          status)
        waiters.wait_for_volume_resource_status(self.snapshots_client,
                                                snapshot_id, status)
        super(SnapshotsActionsTest, self).tearDown()

    def _create_reset_and_force_delete_temp_snapshot(self, status=None):
        # Create snapshot, reset snapshot status,
        # and force delete temp snapshot
        temp_snapshot = self.create_snapshot(volume_id=self.volume['id'])
        if status:
            self.admin_snapshots_client.reset_snapshot_status(
                temp_snapshot['id'], status)
            waiters.wait_for_volume_resource_status(
                self.snapshots_client, temp_snapshot['id'], status)
        self.admin_snapshots_client.force_delete_snapshot(temp_snapshot['id'])
        self.snapshots_client.wait_for_resource_deletion(temp_snapshot['id'])

    def _get_progress_alias(self):
        return 'os-extended-snapshot-attributes:progress'

    @decorators.idempotent_id('3e13ca2f-48ea-49f3-ae1a-488e9180d535')
    def test_reset_snapshot_status(self):
        """Test resetting snapshot status to creating"""
        status = 'creating'
        self.admin_snapshots_client.reset_snapshot_status(
            self.snapshot['id'], status)
        waiters.wait_for_volume_resource_status(self.snapshots_client,
                                                self.snapshot['id'], status)

    @decorators.idempotent_id('41288afd-d463-485e-8f6e-4eea159413eb')
    def test_update_snapshot_status(self):
        """Test updating snapshot

        Update snapshot status to 'error' and progress to '80%'.
        """
        # Reset snapshot status to creating
        status = 'creating'
        self.admin_snapshots_client.reset_snapshot_status(
            self.snapshot['id'], status)
        waiters.wait_for_volume_resource_status(self.snapshots_client,
                                                self.snapshot['id'], status)

        # Update snapshot status to error
        progress = '80%'
        status = 'error'
        progress_alias = self._get_progress_alias()
        self.snapshots_client.update_snapshot_status(self.snapshot['id'],
                                                     status=status,
                                                     progress=progress)
        snapshot_get = self.admin_snapshots_client.show_snapshot(
            self.snapshot['id'])['snapshot']
        self.assertEqual(status, snapshot_get['status'])
        self.assertEqual(progress, snapshot_get[progress_alias])

    @decorators.idempotent_id('05f711b6-e629-4895-8103-7ca069f2073a')
    def test_snapshot_force_delete_when_snapshot_is_creating(self):
        """Test force delete when status of snapshot is creating"""
        self._create_reset_and_force_delete_temp_snapshot('creating')

    @decorators.idempotent_id('92ce8597-b992-43a1-8868-6316b22a969e')
    def test_snapshot_force_delete_when_snapshot_is_deleting(self):
        """Test force delete when status of snapshot is deleting"""
        self._create_reset_and_force_delete_temp_snapshot('deleting')

    @decorators.idempotent_id('645a4a67-a1eb-4e8e-a547-600abac1525d')
    def test_snapshot_force_delete_when_snapshot_is_error(self):
        """Test force delete when status of snapshot is error"""
        self._create_reset_and_force_delete_temp_snapshot('error')

    @decorators.idempotent_id('bf89080f-8129-465e-9327-b2f922666ba5')
    def test_snapshot_force_delete_when_snapshot_is_error_deleting(self):
        """Test force delete when status of snapshot is error_deleting"""
        self._create_reset_and_force_delete_temp_snapshot('error_deleting')
