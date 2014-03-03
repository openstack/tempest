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
from tempest import exceptions
from tempest import test


class DatabaseFlavorsNegativeTest(base.BaseDatabaseTest):

    @classmethod
    def setUpClass(cls):
        super(DatabaseFlavorsNegativeTest, cls).setUpClass()
        cls.client = cls.database_flavors_client

    @test.attr(type=['negative', 'gate'])
    def test_get_non_existent_db_flavor(self):
        # flavor details are not returned for non-existent flavors
        self.assertRaises(exceptions.NotFound,
                          self.client.get_db_flavor_details, -1)
