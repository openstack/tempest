# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from nose.plugins.attrib import attr

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.tests.compute import base
from tempest import whitebox


@attr(type='whitebox')
class ImagesWhiteboxTest(whitebox.ComputeWhiteboxTest, base.BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        super(ImagesWhiteboxTest, cls).setUpClass()
        cls.client = cls.images_client
        cls.connection, cls.meta = cls.get_db_handle_and_meta()
        cls.shared_server = cls.create_server()
        cls.image_ids = []

    @classmethod
    def tearDownClass(cls):
        """Terminate test instances created after a test is executed."""

        for server in cls.servers:
            cls.update_state(server['id'], "active", None)
            resp, body = cls.servers_client.delete_server(server['id'])
            if resp['status'] == '204':
                cls.servers.remove(server)
                cls.servers_client.wait_for_server_termination(server['id'])

        for image_id in cls.image_ids:
            cls.client.delete_image(image_id)
            cls.image_ids.remove(image_id)

    @classmethod
    def update_state(self, server_id, vm_state, task_state, deleted=0):
        """Update states of an instance in database for validation."""
        if not task_state:
            task_state = "NULL"

        instances = self.meta.tables['instances']
        stmt = instances.update().where(instances.c.uuid == server_id).values(
            deleted=deleted,
            vm_state=vm_state,
            task_state=task_state)

        self.connection.execute(stmt, autocommit=True)

    def _test_create_image_409_base(self, vm_state, task_state, deleted=0):
        """Base method for create image tests based on vm and task states."""
        try:
            self.update_state(self.shared_server['id'], vm_state,
                              task_state, deleted)

            image_name = rand_name('snap-')
            self.assertRaises(exceptions.Duplicate,
                              self.client.create_image,
                              self.shared_server['id'], image_name)
        except Exception:
            self.fail("Should not allow create image when vm_state=%s and "
                      "task_state=%s" % (vm_state, task_state))
        finally:
            self.update_state(self.shared_server['id'], 'active', None)

    def test_create_image_when_vm_eq_building_task_eq_scheduling(self):
        # 409 error when instance states are building,scheduling
        self._test_create_image_409_base("building", "scheduling")

    def test_create_image_when_vm_eq_building_task_eq_networking(self):
        # 409 error when instance states are building,networking
        self._test_create_image_409_base("building", "networking")

    def test_create_image_when_vm_eq_building_task_eq_bdm(self):
        # 409 error when instance states are building,block_device_mapping
        self._test_create_image_409_base("building", "block_device_mapping")

    def test_create_image_when_vm_eq_building_task_eq_spawning(self):
        # 409 error when instance states are building,spawning
        self._test_create_image_409_base("building", "spawning")

    def test_create_image_when_vm_eq_active_task_eq_image_backup(self):
        # 409 error when instance states are active,image_backup
        self._test_create_image_409_base("active", "image_backup")

    def test_create_image_when_vm_eq_resized_task_eq_resize_prep(self):
        # 409 error when instance states are resized,resize_prep
        self._test_create_image_409_base("resized", "resize_prep")

    def test_create_image_when_vm_eq_resized_task_eq_resize_migrating(self):
        # 409 error when instance states are resized,resize_migrating
        self._test_create_image_409_base("resized", "resize_migrating")

    def test_create_image_when_vm_eq_resized_task_eq_resize_migrated(self):
        # 409 error when instance states are resized,resize_migrated
        self._test_create_image_409_base("resized", "resize_migrated")

    def test_create_image_when_vm_eq_resized_task_eq_resize_finish(self):
        # 409 error when instance states are resized,resize_finish
        self._test_create_image_409_base("resized", "resize_finish")

    def test_create_image_when_vm_eq_resized_task_eq_resize_reverting(self):
        # 409 error when instance states are resized,resize_reverting
        self._test_create_image_409_base("resized", "resize_reverting")

    def test_create_image_when_vm_eq_resized_task_eq_resize_confirming(self):
        # 409 error when instance states are resized,resize_confirming
        self._test_create_image_409_base("resized", "resize_confirming")

    def test_create_image_when_vm_eq_active_task_eq_resize_verify(self):
        # 409 error when instance states are active,resize_verify
        self._test_create_image_409_base("active", "resize_verify")

    def test_create_image_when_vm_eq_active_task_eq_updating_password(self):
        # 409 error when instance states are active,updating_password
        self._test_create_image_409_base("active", "updating_password")

    def test_create_image_when_vm_eq_active_task_eq_rebuilding(self):
        # 409 error when instance states are active,rebuilding
        self._test_create_image_409_base("active", "rebuilding")

    def test_create_image_when_vm_eq_active_task_eq_rebooting(self):
        # 409 error when instance states are active,rebooting
        self._test_create_image_409_base("active", "rebooting")

    def test_create_image_when_vm_eq_building_task_eq_deleting(self):
        # 409 error when instance states are building,deleting
        self._test_create_image_409_base("building", "deleting")

    def test_create_image_when_vm_eq_active_task_eq_deleting(self):
        # 409 error when instance states are active,deleting
        self._test_create_image_409_base("active", "deleting")

    def test_create_image_when_vm_eq_error_task_eq_building(self):
        # 409 error when instance states are error,building
        self._test_create_image_409_base("error", "building")

    def test_create_image_when_vm_eq_error_task_eq_none(self):
        # 409 error when instance states are error,None
        self._test_create_image_409_base("error", None)

    def test_create_image_when_vm_eq_deleted_task_eq_none(self):
        # 409 error when instance states are deleted,None
        self._test_create_image_409_base("deleted", None)

    def test_create_image_when_vm_eq_resized_task_eq_none(self):
        # 409 error when instance states are resized,None
        self._test_create_image_409_base("resized", None)

    def test_create_image_when_vm_eq_error_task_eq_resize_prep(self):
        # 409 error when instance states are error,resize_prep
        self._test_create_image_409_base("error", "resize_prep")
