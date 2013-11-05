# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.api.volume.base import BaseVolumeAdminTest
from tempest.common.utils import data_utils as utils
from tempest.test import attr


class VolumesActionsTest(BaseVolumeAdminTest):
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(VolumesActionsTest, cls).setUpClass()
        cls.client = cls.volumes_client

        # Create admin volume client
        cls.admin_volume_client = cls.os_adm.volumes_client

        # Create a test shared volume for tests
        vol_name = utils.rand_name(cls.__name__ + '-Volume-')

        resp, cls.volume = cls.client.create_volume(size=1,
                                                    display_name=vol_name)
        cls.client.wait_for_volume_status(cls.volume['id'], 'available')

    @classmethod
    def tearDownClass(cls):
        # Delete the test volume
        cls.client.delete_volume(cls.volume['id'])
        cls.client.wait_for_resource_deletion(cls.volume['id'])

        super(VolumesActionsTest, cls).tearDownClass()

    def _reset_volume_status(self, volume_id, status):
        #Reset the volume status
        resp, body = self.admin_volume_client.reset_volume_status(volume_id,
                                                                  status)
        return resp, body

    def tearDown(self):
        # Set volume's status to available after test
        self._reset_volume_status(self.volume['id'], 'available')
        super(VolumesActionsTest, self).tearDown()

    @attr(type='gate')
    def test_volume_reset_status(self):
        # test volume reset status : available->error->available
        resp, body = self._reset_volume_status(self.volume['id'], 'error')
        self.assertEqual(202, resp.status)
        resp_get, volume_get = self.admin_volume_client.get_volume(
            self.volume['id'])
        self.assertEqual('error', volume_get['status'])

    @attr(type='gate')
    def test_volume_begin_detaching(self):
        # test volume begin detaching : available -> detaching -> available
        resp, body = self.client.volume_begin_detaching(self.volume['id'])
        self.assertEqual(202, resp.status)
        resp_get, volume_get = self.client.get_volume(self.volume['id'])
        self.assertEqual('detaching', volume_get['status'])

    @attr(type='gate')
    def test_volume_roll_detaching(self):
        # test volume roll detaching : detaching -> in-use -> available
        resp, body = self.client.volume_begin_detaching(self.volume['id'])
        self.assertEqual(202, resp.status)
        resp, body = self.client.volume_roll_detaching(self.volume['id'])
        self.assertEqual(202, resp.status)
        resp_get, volume_get = self.client.get_volume(self.volume['id'])
        self.assertEqual('in-use', volume_get['status'])


class VolumesActionsTestXML(VolumesActionsTest):
    _interface = "xml"
