# -*- coding: utf-8 -*-
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

from tempest.api.baremetal.admin import base
from tempest.common.utils import data_utils
from tempest import exceptions as exc
from tempest import test


class TestChassis(base.BaseBaremetalTest):
    """Tests for chassis."""

    @classmethod
    def setUpClass(cls):
        super(TestChassis, cls).setUpClass()
        _, cls.chassis = cls.create_chassis()

    def _assertExpected(self, expected, actual):
        # Check if not expected keys/values exists in actual response body
        for key, value in expected.iteritems():
            if key not in ('created_at', 'updated_at'):
                self.assertIn(key, actual)
                self.assertEqual(value, actual[key])

    @test.attr(type='smoke')
    def test_create_chassis(self):
        descr = data_utils.rand_name('test-chassis-')
        resp, chassis = self.create_chassis(description=descr)
        self.assertEqual('201', resp['status'])
        self.assertEqual(chassis['description'], descr)

    @test.attr(type='smoke')
    def test_create_chassis_unicode_description(self):
        # Use a unicode string for testing:
        # 'We ♡ OpenStack in Ukraine'
        descr = u'В Україні ♡ OpenStack!'
        resp, chassis = self.create_chassis(description=descr)
        self.assertEqual('201', resp['status'])
        self.assertEqual(chassis['description'], descr)

    @test.attr(type='smoke')
    def test_show_chassis(self):
        resp, chassis = self.client.show_chassis(self.chassis['uuid'])
        self.assertEqual('200', resp['status'])
        self._assertExpected(self.chassis, chassis)

    @test.attr(type="smoke")
    def test_list_chassis(self):
        resp, body = self.client.list_chassis()
        self.assertEqual('200', resp['status'])
        self.assertIn(self.chassis['uuid'],
                      [i['uuid'] for i in body['chassis']])

    @test.attr(type='smoke')
    def test_delete_chassis(self):
        resp, body = self.create_chassis()
        uuid = body['uuid']

        resp = self.delete_chassis(uuid)
        self.assertEqual('204', resp['status'])
        self.assertRaises(exc.NotFound, self.client.show_chassis, uuid)

    @test.attr(type='smoke')
    def test_update_chassis(self):
        resp, body = self.create_chassis()
        uuid = body['uuid']

        new_description = data_utils.rand_name('new-description-')
        resp, body = (self.client.update_chassis(uuid,
                      description=new_description))
        self.assertEqual('200', resp['status'])
        resp, chassis = self.client.show_chassis(uuid)
        self.assertEqual(chassis['description'], new_description)
