# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.api.baremetal import base
from tempest.common.utils import data_utils
from tempest import exceptions as exc
from tempest import test


class TestChassis(base.BaseBaremetalTest):
    """Tests for chassis."""

    @test.attr(type='smoke')
    def test_create_chassis(self):
        descr = data_utils.rand_name('test-chassis-')
        ch = self.create_chassis(description=descr)['chassis']

        self.assertEqual(ch['description'], descr)

    @test.attr(type='smoke')
    def test_create_chassis_unicode_description(self):
        # Use a unicode string for testing:
        # 'We ♡ OpenStack in Ukraine'
        descr = u'В Україні ♡ OpenStack!'
        ch = self.create_chassis(description=descr)['chassis']

        self.assertEqual(ch['description'], descr)

    @test.attr(type='smoke')
    def test_show_chassis(self):
        descr = data_utils.rand_name('test-chassis-')
        uuid = self.create_chassis(description=descr)['chassis']['uuid']

        resp, chassis = self.client.show_chassis(uuid)

        self.assertEqual(chassis['uuid'], uuid)
        self.assertEqual(chassis['description'], descr)

    @test.attr(type="smoke")
    def test_list_chassis(self):
        created_ids = [self.create_chassis()['chassis']['uuid']
                       for i in range(0, 5)]

        resp, body = self.client.list_chassis()
        loaded_ids = [ch['uuid'] for ch in body['chassis']]

        for i in created_ids:
            self.assertIn(i, loaded_ids)

    @test.attr(type='smoke')
    def test_delete_chassis(self):
        uuid = self.create_chassis()['chassis']['uuid']

        self.delete_chassis(uuid)

        self.assertRaises(exc.NotFound, self.client.show_chassis, uuid)

    @test.attr(type='smoke')
    def test_update_chassis(self):
        chassis_id = self.create_chassis()['chassis']['uuid']

        new_description = data_utils.rand_name('new-description-')
        self.client.update_chassis(chassis_id, description=new_description)

        resp, chassis = self.client.show_chassis(chassis_id)
        self.assertEqual(chassis['description'], new_description)
