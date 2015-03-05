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


class DatabaseLimitsTest(base.BaseDatabaseTest):

    @classmethod
    def resource_setup(cls):
        super(DatabaseLimitsTest, cls).resource_setup()
        cls.client = cls.database_limits_client

    @test.attr(type='smoke')
    @test.idempotent_id('73024538-f316-4829-b3e9-b459290e137a')
    def test_absolute_limits(self):
        # Test to verify if all absolute limit paramaters are
        # present when verb is ABSOLUTE
        limits = self.client.list_db_limits()
        expected_abs_limits = ['max_backups', 'max_volumes',
                               'max_instances', 'verb']
        absolute_limit = [l for l in limits
                          if l['verb'] == 'ABSOLUTE']
        self.assertEqual(1, len(absolute_limit), "One ABSOLUTE limit "
                         "verb is allowed. Fetched %s"
                         % len(absolute_limit))
        actual_abs_limits = absolute_limit[0].keys()
        missing_abs_limit = set(expected_abs_limits) - set(actual_abs_limits)
        self.assertEmpty(missing_abs_limit,
                         "Failed to find the following absolute limit(s)"
                         " in a fetched list: %s" %
                         ', '.join(str(a) for a in missing_abs_limit))
