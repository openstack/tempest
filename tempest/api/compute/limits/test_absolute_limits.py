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
from tempest.lib import decorators


class AbsoluteLimitsTestJSON(base.BaseV2ComputeTest):
    """Test compute absolute limits

    Test compute absolute limits with compute microversion less than 2.57
    """

    max_microversion = '2.56'

    @classmethod
    def setup_clients(cls):
        super(AbsoluteLimitsTestJSON, cls).setup_clients()
        cls.client = cls.limits_client

    @decorators.idempotent_id('b54c66af-6ab6-4cf0-a9e5-a0cb58d75e0b')
    def test_absLimits_get(self):
        """Test getting nova absolute limits"""
        # To check if all limits are present in the response (will be checked
        # by schema)
        self.client.show_limits()


class AbsoluteLimitsV257TestJSON(base.BaseV2ComputeTest):
    """Test compute absolute limits

    Test compute absolute limits with compute microversion greater than 2.56
    """
    min_microversion = '2.57'
    max_microversion = 'latest'

    # NOTE(felipemonteiro): This class tests the Absolute Limits APIs
    # response schema for the 2.57 microversion.
