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
from tempest.common.utils import data_utils
from tempest.test import attr


class SnapshotsActionsTest(base.BaseVolumeV1AdminTest):
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(SnapshotsActionsTest, cls).setUpClass()
        cls.client = cls.snapshots_client

        # Create admin volume client
        cls.admin_snapshots_client = cls.os_adm.snapshots_client

        # Create a test shared volume for tests
        vol_name = data_utils.rand_name(cls.__name__ + '-Volume-')
        resp_vol, cls.volume = \
            cls.volumes_client.create_volume(size=1, display_name=vol_name)
        cls.volumes_client.wait_for_volume_status(cls.volume['id'],
                                                  'available')

        # Create a test shared snapshot for tests
        snap_name = data_utils.rand_name(cls.__name__ + '-Snapshot-')
        resp_snap, cls.snapshot = \
            cls.client.create_snapshot(cls.volume['id'],
                                       display_name=snap_name)
        cls.client.wait_for_snapshot_status(cls.snapshot['id'],
                                            'available')

    @classmethod
    def tearDownClass(cls):
        # Delete the test snapshot
        cls.client.delete_snapshot(cls.snapshot['id'])
        cls.client.wait_for_resource_deletion(cls.snapshot['id'])

        # Delete the test volume
        cls.volumes_client.delete_volume(cls.volume['id'])
        cls.volumes_client.wait_for_resource_deletion(cls.volume['id'])

        super(SnapshotsActionsTest, cls).tearDownClass()

    def tearDown(self):
        # Set snapshot's status to available after test
        status = 'available'
        snapshot_id = self.snapshot['id']
        self.admin_snapshots_client.reset_snapshot_status(snapshot_id,
                                                          status)
        super(SnapshotsActionsTest, self).tearDown()

    def _create_reset_and_force_delete_temp_snapshot(self, status=None):
        # Create snapshot, reset snapshot status,
        # and force delete temp snapshot
        temp_snapshot = self.create_snapshot(self.volume['id'])
        if status:
            resp, body = self.admin_snapshots_client.\
                reset_snapshot_status(temp_snapshot['id'], status)
            self.assertEqual(202, resp.status)
        resp_delete, volume_delete = self.admin_snapshots_client.\
            force_delete_snapshot(temp_snapshot['id'])
        self.assertEqual(202, resp_delete.status)
        self.client.wait_for_resource_deletion(temp_snapshot['id'])

    def _get_progress_alias(self):
        return 'os-extended-snapshot-attributes:progress'

    @attr(type='gate')
    def test_reset_snapshot_status(self):
        # Reset snapshot status to creating
        status = 'creating'
        resp, body = self.admin_snapshots_client.\
            reset_snapshot_status(self.snapshot['id'], status)
        self.assertEqual(202, resp.status)
        resp_get, snapshot_get \
            = self.admin_snapshots_client.get_snapshot(self.snapshot['id'])
        self.assertEqual(200, resp_get.status)
        self.assertEqual(status, snapshot_get['status'])

    @attr(type='gate')
    def test_update_snapshot_status(self):
        # Reset snapshot status to creating
        status = 'creating'
        self.admin_snapshots_client.\
            reset_snapshot_status(self.snapshot['id'], status)

        # Update snapshot status to error
        progress = '80%'
        status = 'error'
        progress_alias = self._get_progress_alias()
        resp, body = self.client.update_snapshot_status(self.snapshot['id'],
                                                        status, progress)
        self.assertEqual(202, resp.status)
        resp_get, snapshot_get \
            = self.admin_snapshots_client.get_snapshot(self.snapshot['id'])
        self.assertEqual(200, resp_get.status)
        self.assertEqual(status, snapshot_get['status'])
        self.assertEqual(progress, snapshot_get[progress_alias])

    @attr(type='gate')
    def test_snapshot_force_delete_when_snapshot_is_creating(self):
        # test force delete when status of snapshot is creating
        self._create_reset_and_force_delete_temp_snapshot('creating')

    @attr(type='gate')
    def test_snapshot_force_delete_when_snapshot_is_deleting(self):
        # test force delete when status of snapshot is deleting
        self._create_reset_and_force_delete_temp_snapshot('deleting')

    @attr(type='gate')
    def test_snapshot_force_delete_when_snapshot_is_error(self):
        # test force delete when status of snapshot is error
        self._create_reset_and_force_delete_temp_snapshot('error')

    @attr(type='gate')
    def test_snapshot_force_delete_when_snapshot_is_error_deleting(self):
        # test force delete when status of snapshot is error_deleting
        self._create_reset_and_force_delete_temp_snapshot('error_deleting')


class SnapshotsActionsTestXML(SnapshotsActionsTest):
    _interface = "xml"

    def _get_progress_alias(self):
        return '{http://docs.openstack.org/volume/ext' \
               '/extended_snapshot_attributes/api/v1}progress'
