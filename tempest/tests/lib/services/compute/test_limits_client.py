# Copyright 2015 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.compute import limits_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestLimitsClient(base.BaseComputeServiceTest):

    def setUp(self):
        super(TestLimitsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = limits_client.LimitsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_show_limits(self, bytes_body=False):
        expected = {
            "limits": {
                "rate": [],
                "absolute": {
                    "maxServerMeta": 128,
                    "maxPersonality": 5,
                    "totalServerGroupsUsed": 0,
                    "maxImageMeta": 128,
                    "maxPersonalitySize": 10240,
                    "maxServerGroups": 10,
                    "maxSecurityGroupRules": 20,
                    "maxTotalKeypairs": 100,
                    "totalCoresUsed": 0,
                    "totalRAMUsed": 0,
                    "totalInstancesUsed": 0,
                    "maxSecurityGroups": 10,
                    "totalFloatingIpsUsed": 0,
                    "maxTotalCores": 20,
                    "totalSecurityGroupsUsed": 0,
                    "maxTotalFloatingIps": 10,
                    "maxTotalInstances": 10,
                    "maxTotalRAMSize": 51200,
                    "maxServerGroupMembers": 10
                    }
            }
        }

        self.check_service_client_function(
            self.client.show_limits,
            'tempest.lib.common.rest_client.RestClient.get',
            expected,
            bytes_body)

    def test_show_limits_with_str_body(self):
        self._test_show_limits()

    def test_show_limits_with_bytes_body(self):
        self._test_show_limits(bytes_body=True)
