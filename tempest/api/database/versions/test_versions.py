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
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(DatabaseVersionsTest, cls).setUpClass()
        cls.client = cls.database_versions_client

    @test.attr(type='smoke')
    def test_list_db_versions(self):
        resp, versions = self.client.list_db_versions()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(versions) > 0, "No database versions found")
        # List of all versions should contain the current version, and there
        # should only be one 'current' version
        current_versions = list()
        for version in versions:
            if 'CURRENT' == version['status']:
                current_versions.append(version['id'])
        self.assertEqual(1, len(current_versions))
        self.assertIn(self.db_current_version, current_versions)
