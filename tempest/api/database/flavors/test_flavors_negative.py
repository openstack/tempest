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

from tempest_lib import exceptions as lib_exc

from tempest.api.database import base
from tempest import test


class DatabaseFlavorsNegativeTest(base.BaseDatabaseTest):

    @classmethod
    def setup_clients(cls):
        super(DatabaseFlavorsNegativeTest, cls).setup_clients()
        cls.client = cls.database_flavors_client

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f8e7b721-373f-4a64-8e9c-5327e975af3e')
    def test_get_non_existent_db_flavor(self):
        # flavor details are not returned for non-existent flavors
        self.assertRaises(lib_exc.NotFound,
                          self.client.get_db_flavor_details, -1)
