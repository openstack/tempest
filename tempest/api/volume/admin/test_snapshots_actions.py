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

from tempest_lib.common.utils import data_utils

from tempest.api.volume import base
from tempest import test


class SnapshotsActionsV2Test(base.BaseVolumeAdminTest):

    @classmethod
    def setup_clients(cls):
        super(SnapshotsActionsV2Test, cls).setup_clients()
        cls.client = cls.snapshots_client

    @classmethod
    def resource_setup(cls):
        super(SnapshotsActionsV2Test, cls).resource_setup()

        # Create a test shared volume for tests
        vol_name = data_utils.rand_name(cls.__name__ + '-Volume')
        cls.name_field = cls.special_fields['name_field']
        params = {cls.name_field: vol_name}
        cls.volume = \
            cls.volumes_client.create_volume(**params)
        cls.volumes_client.wait_for_volume_status(cls.volume['id'],
                                                  'available')

        # Create a test shared snapshot for tests
        snap_name = data_utils.rand_name(cls.__name__ + '-Snapshot')
        params = {cls.name_field: snap_name}
        cls.snapshot = \
            cls.client.create_snapshot(cls.volume['id'], **params)
        cls.client.wait_for_snapshot_status(cls.snapshot['id'],
                                            'available')

    @classmethod
    def resource_cleanup(cls):
        # Delete the test snapshot
        cls.client.delete_snapshot(cls.snapshot['id'])
        cls.client.wait_for_resource_deletion(cls.snapshot['id'])

        # Delete the test volume
        cls.volumes_client.delete_volume(cls.volume['id'])
        cls.volumes_client.wait_for_resource_deletion(cls.volume['id'])

        super(SnapshotsActionsV2Test, cls).resource_cleanup()

    def tearDown(self):
        # Set snapshot's status to available after test
        status = 'available'
        snapshot_id = self.snapshot['id']
        self.admin_snapshots_client.reset_snapshot_status(snapshot_id,
                                                          status)
        super(SnapshotsActionsV2Test, self).tearDown()

    def _create_reset_and_force_delete_temp_snapshot(self, status=None):
        # Create snapshot, reset snapshot status,
        # and force delete temp snapshot
        temp_snapshot = self.create_snapshot(self.volume['id'])
        if status:
            self.admin_snapshots_client.\
                reset_snapshot_status(temp_snapshot['id'], status)
        self.admin_snapshots_client.\
            force_delete_snapshot(temp_snapshot['id'])
        self.client.wait_for_resource_deletion(temp_snapshot['id'])

    def _get_progress_alias(self):
        return 'os-extended-snapshot-attributes:progress'

    @test.attr(type='gate')
    @test.idempotent_id('3e13ca2f-48ea-49f3-ae1a-488e9180d535')
    def test_reset_snapshot_status(self):
        # Reset snapshot status to creating
        status = 'creating'
        self.admin_snapshots_client.\
            reset_snapshot_status(self.snapshot['id'], status)
        snapshot_get \
            = self.admin_snapshots_client.show_snapshot(self.snapshot['id'])
        self.assertEqual(status, snapshot_get['status'])

    @test.attr(type='gate')
    @test.idempotent_id('41288afd-d463-485e-8f6e-4eea159413eb')
    def test_update_snapshot_status(self):
        # Reset snapshot status to creating
        status = 'creating'
        self.admin_snapshots_client.\
            reset_snapshot_status(self.snapshot['id'], status)

        # Update snapshot status to error
        progress = '80%'
        status = 'error'
        progress_alias = self._get_progress_alias()
        self.client.update_snapshot_status(self.snapshot['id'],
                                           status, progress)
        snapshot_get \
            = self.admin_snapshots_client.show_snapshot(self.snapshot['id'])
        self.assertEqual(status, snapshot_get['status'])
        self.assertEqual(progress, snapshot_get[progress_alias])

    @test.attr(type='gate')
    @test.idempotent_id('05f711b6-e629-4895-8103-7ca069f2073a')
    def test_snapshot_force_delete_when_snapshot_is_creating(self):
        # test force delete when status of snapshot is creating
        self._create_reset_and_force_delete_temp_snapshot('creating')

    @test.attr(type='gate')
    @test.idempotent_id('92ce8597-b992-43a1-8868-6316b22a969e')
    def test_snapshot_force_delete_when_snapshot_is_deleting(self):
        # test force delete when status of snapshot is deleting
        self._create_reset_and_force_delete_temp_snapshot('deleting')

    @test.attr(type='gate')
    @test.idempotent_id('645a4a67-a1eb-4e8e-a547-600abac1525d')
    def test_snapshot_force_delete_when_snapshot_is_error(self):
        # test force delete when status of snapshot is error
        self._create_reset_and_force_delete_temp_snapshot('error')

    @test.attr(type='gate')
    @test.idempotent_id('bf89080f-8129-465e-9327-b2f922666ba5')
    def test_snapshot_force_delete_when_snapshot_is_error_deleting(self):
        # test force delete when status of snapshot is error_deleting
        self._create_reset_and_force_delete_temp_snapshot('error_deleting')


class SnapshotsActionsV1Test(SnapshotsActionsV2Test):
    _api_version = 1
