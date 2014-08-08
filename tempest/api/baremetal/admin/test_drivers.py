# Copyright 2014 NEC Corporation. All rights reserved.
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

from tempest.api.baremetal.admin import base
from tempest import config
from tempest import test

CONF = config.CONF


class TestDrivers(base.BaseBaremetalTest):
    """Tests for drivers."""
    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(TestDrivers, cls).setUpClass()
        cls.driver_name = CONF.baremetal.driver

    @test.attr(type="smoke")
    def test_list_drivers(self):
        resp, drivers = self.client.list_drivers()
        self.assertEqual('200', resp['status'])
        self.assertIn(self.driver_name,
                      [d['name'] for d in drivers['drivers']])

    @test.attr(type="smoke")
    def test_show_driver(self):
        resp, driver = self.client.show_driver(self.driver_name)
        self.assertEqual('200', resp['status'])
        self.assertEqual(self.driver_name, driver['name'])
