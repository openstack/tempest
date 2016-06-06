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

from tempest.lib.services.compute import agents_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestAgentsClient(base.BaseServiceTest):
    FAKE_CREATE_AGENT = {
        "agent": {
            "url": "http://foo.com",
            "hypervisor": "kvm",
            "md5hash": "md5",
            "version": "2",
            "architecture": "x86_64",
            "os": "linux",
            "agent_id": 1
        }
    }

    FAKE_UPDATE_AGENT = {
        "agent": {
            "url": "http://foo.com",
            "md5hash": "md5",
            "version": "2",
            "agent_id": 1
        }
    }

    def setUp(self):
        super(TestAgentsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = agents_client.AgentsClient(fake_auth,
                                                 'compute', 'regionOne')

    def _test_list_agents(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_agents,
            'tempest.lib.common.rest_client.RestClient.get',
            {"agents": []},
            bytes_body)
        self.check_service_client_function(
            self.client.list_agents,
            'tempest.lib.common.rest_client.RestClient.get',
            {"agents": []},
            bytes_body,
            hypervisor="kvm")

    def _test_create_agent(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_agent,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_AGENT,
            bytes_body,
            url="http://foo.com", hypervisor="kvm", md5hash="md5",
            version="2", architecture="x86_64", os="linux")

    def _test_delete_agent(self):
        self.check_service_client_function(
            self.client.delete_agent,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, agent_id="1")

    def _test_update_agent(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_agent,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_AGENT,
            bytes_body,
            agent_id="1", url="http://foo.com", md5hash="md5", version="2")

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
