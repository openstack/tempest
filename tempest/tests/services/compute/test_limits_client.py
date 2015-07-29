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

import httplib2

from oslo_serialization import jsonutils as json
from oslotest import mockpatch

from tempest.services.compute.json import limits_client
from tempest.tests import base
from tempest.tests import fake_auth_provider


class TestLimitsClient(base.TestCase):

    def setUp(self):
        super(TestLimitsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = limits_client.LimitsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_show_limits(self, bytes_body=False):
        expected = {"rate": [],
                    "absolute": {"maxServerMeta": 128,
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
                                 "maxServerGroupMembers": 10}}
        serialized_body = json.dumps({"limits": expected})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.show_limits()
        self.assertEqual(expected, resp)

    def test_show_limits_with_str_body(self):
        self._test_show_limits()

    def test_show_limits_with_bytes_body(self):
        self._test_show_limits(bytes_body=True)
