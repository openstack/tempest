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


class DatabaseVersionsTest(base.BaseDatabaseTest):

    @classmethod
    def setup_clients(cls):
        super(DatabaseVersionsTest, cls).setup_clients()
        cls.client = cls.database_versions_client

    @test.attr(type='smoke')
    @test.idempotent_id('6952cd77-90cd-4dca-bb60-8e2c797940cf')
    def test_list_db_versions(self):
        versions = self.client.list_db_versions()
        self.assertTrue(len(versions) > 0, "No database versions found")
        # List of all versions should contain the current version, and there
        # should only be one 'current' version
        current_versions = list()
        for version in versions:
            if 'CURRENT' == version['status']:
                current_versions.append(version['id'])
        self.assertEqual(1, len(current_versions))
        self.assertIn(self.db_current_version, current_versions)
