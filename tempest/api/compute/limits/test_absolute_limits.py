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
from tempest import test


class AbsoluteLimitsTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(AbsoluteLimitsTestJSON, cls).setup_clients()
        cls.client = cls.limits_client

    @test.attr(type='gate')
    @test.idempotent_id('b54c66af-6ab6-4cf0-a9e5-a0cb58d75e0b')
    def test_absLimits_get(self):
        # To check if all limits are present in the response
        absolute_limits = self.client.get_absolute_limits()
        expected_elements = ['maxImageMeta', 'maxPersonality',
                             'maxPersonalitySize',
                             'maxServerMeta', 'maxTotalCores',
                             'maxTotalFloatingIps', 'maxSecurityGroups',
                             'maxSecurityGroupRules', 'maxTotalInstances',
                             'maxTotalKeypairs', 'maxTotalRAMSize',
                             'totalCoresUsed', 'totalFloatingIpsUsed',
                             'totalSecurityGroupsUsed', 'totalInstancesUsed',
                             'totalRAMUsed']
        # check whether all expected elements exist
        missing_elements =\
            [ele for ele in expected_elements if ele not in absolute_limits]
        self.assertEqual(0, len(missing_elements),
                         "Failed to find element %s in absolute limits list"
                         % ', '.join(ele for ele in missing_elements))
