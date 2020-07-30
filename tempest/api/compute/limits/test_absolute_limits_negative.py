# Copyright 2012 OpenStack Foundation
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

from tempest.api.compute import base
from tempest.common import tempest_fixtures as fixtures
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class AbsoluteLimitsNegativeTestJSON(base.BaseV2ComputeTest):
    """Negative tests of nova absolute limits"""

    def setUp(self):
        # NOTE(mriedem): Avoid conflicts with os-quota-class-sets tests.
        self.useFixture(fixtures.LockFixture('compute_quotas'))
        super(AbsoluteLimitsNegativeTestJSON, self).setUp()

    @classmethod
    def setup_clients(cls):
        super(AbsoluteLimitsNegativeTestJSON, cls).setup_clients()
        cls.client = cls.limits_client

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('215cd465-d8ae-49c9-bf33-9c911913a5c8')
    def test_max_metadata_exceed_limit(self):
        """Test creating server with metadata over limit should fail

        We should not create server with metadata over maxServerMeta limit
        """
        # Get max limit value
        limits = self.client.show_limits()['limits']
        max_meta = limits['absolute']['maxServerMeta']

        # No point in running this test if there is no limit.
        if max_meta == -1:
            raise self.skipException('no limit for maxServerMeta')

        # Create server should fail, since we are passing > metadata Limit!
        max_meta_data = max_meta + 1

        meta_data = {}
        for xx in range(max_meta_data):
            meta_data[str(xx)] = str(xx)

        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised when out of quota
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.create_test_server, metadata=meta_data)
