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

from oslotest import mockpatch

from tempest.services.compute.json import agents_client
from tempest.tests import base
from tempest.tests import fake_auth_provider
from tempest.tests import fake_config


class TestAgentsClient(base.TestCase):

    def setUp(self):
        super(TestAgentsClient, self).setUp()
        self.useFixture(fake_config.ConfigFixture())
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = agents_client.AgentsClient(fake_auth,
                                                 'compute', 'regionOne')

    def _test_list_agents(self, bytes_body=False):
        body = '{"agents": []}'
        if bytes_body:
            body = bytes(body.encode('utf-8'))
        expected = []
        response = (httplib2.Response({'status': 200}), body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=response))
        self.assertEqual(expected, self.client.list_agents())

    def test_list_agents_with_str_body(self):
        self._test_list_agents()

    def test_list_agents_with_bytes_body(self):
        self._test_list_agents(bytes_body=True)
