# Copyright 2014 OpenStack Foundation
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

from tempest.api.database import base
from tempest import test


class DatabaseFlavorsTest(base.BaseDatabaseTest):

    @classmethod
    def setUpClass(cls):
        super(DatabaseFlavorsTest, cls).setUpClass()
        cls.client = cls.database_flavors_client

    @test.attr(type='smoke')
    def test_get_db_flavor(self):
        # The expected flavor details should be returned
        resp, flavor = self.client.get_db_flavor_details(self.db_flavor_ref)
        self.assertEqual(200, resp.status)
        self.assertEqual(self.db_flavor_ref, str(flavor['id']))
        self.assertIn('ram', flavor)
        self.assertIn('links', flavor)
        self.assertIn('name', flavor)

    @test.attr(type='smoke')
    def test_list_db_flavors(self):
        resp, flavor = self.client.get_db_flavor_details(self.db_flavor_ref)
        self.assertEqual(200, resp.status)
        # List of all flavors should contain the expected flavor
        resp, flavors = self.client.list_db_flavors()
        self.assertEqual(200, resp.status)
        self.assertIn(flavor, flavors)

    def _check_values(self, names, db_flavor, os_flavor, in_db=True):
        for name in names:
            self.assertIn(name, os_flavor)
            if in_db:
                self.assertIn(name, db_flavor)
                self.assertEqual(str(db_flavor[name]), str(os_flavor[name]),
                                 "DB flavor differs from OS on '%s' value"
                                 % name)
            else:
                self.assertNotIn(name, db_flavor)

    @test.attr(type='smoke')
    @test.services('compute')
    def test_compare_db_flavors_with_os(self):
        resp, db_flavors = self.client.list_db_flavors()
        self.assertEqual(200, resp.status)
        resp, os_flavors = self.os_flavors_client.list_flavors_with_detail()
        self.assertEqual(200, resp.status)
        self.assertEqual(len(os_flavors), len(db_flavors),
                         "OS flavors %s do not match DB flavors %s" %
                         (os_flavors, db_flavors))
        for os_flavor in os_flavors:
            resp, db_flavor =\
                self.client.get_db_flavor_details(os_flavor['id'])
            self.assertEqual(200, resp.status)
            self._check_values(['id', 'name', 'ram'], db_flavor, os_flavor)
            self._check_values(['disk', 'vcpus', 'swap'], db_flavor, os_flavor,
                               in_db=False)
