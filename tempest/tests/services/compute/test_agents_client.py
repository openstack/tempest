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

from tempest.services.compute.json import agents_client
from tempest.tests import base
from tempest.tests import fake_auth_provider


class TestAgentsClient(base.TestCase):

    def setUp(self):
        super(TestAgentsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = agents_client.AgentsClient(fake_auth,
                                                 'compute', 'regionOne')

    def _test_list_agents(self, bytes_body=False):
        body = '{"agents": []}'
        if bytes_body:
            body = body.encode('utf-8')
        expected = []
        response = (httplib2.Response({'status': 200}), body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=response))
        self.assertEqual(expected, self.client.list_agents())

    def _test_create_agent(self, bytes_body=False):
        expected = {"url": "http://foo.com", "hypervisor": "kvm",
                    "md5hash": "md5", "version": "2", "architecture": "x86_64",
                    "os": "linux", "agent_id": 1}
        serialized_body = json.dumps({"agent": expected})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.post',
            return_value=mocked_resp))
        resp = self.client.create_agent(
            url="http://foo.com", hypervisor="kvm", md5hash="md5",
            version="2", architecture="x86_64", os="linux"
        )
        self.assertEqual(expected, resp)

    def _test_delete_agent(self):
        mocked_resp = (httplib2.Response({'status': 200}), None)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.delete',
            return_value=mocked_resp))
        self.client.delete_agent("1")

    def _test_update_agent(self, bytes_body=False):
        expected = {"url": "http://foo.com", "md5hash": "md5", "version": "2",
                    "agent_id": 1}
        serialized_body = json.dumps({"agent": expected})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.put',
            return_value=mocked_resp))
        resp = self.client.update_agent(
            "1", url="http://foo.com", md5hash="md5", version="2"
        )
        self.assertEqual(expected, resp)

    def test_list_agents_with_str_body(self):
        self._test_list_agents()

    def test_list_agents_with_bytes_body(self):
        self._test_list_agents(bytes_body=True)

    def test_create_agent_with_str_body(self):
        self._test_create_agent()

    def test_create_agent_with_bytes_body(self):
        self._test_create_agent(bytes_body=True)

    def test_delete_agent(self):
        self._test_delete_agent()

    def test_update_agent_with_str_body(self):
        self._test_update_agent()

    def test_update_agent_with_bytes_body(self):
        self._test_update_agent(bytes_body=True)
