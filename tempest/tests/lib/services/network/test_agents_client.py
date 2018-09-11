# Copyright 2018 AT&T Corporation.
# All rights reserved.
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

from tempest.lib.services.network import agents_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestAgentsClient(base.BaseServiceTest):

    FAKE_AGENT_ID = "d32019d3-bc6e-4319-9c1d-6123f4135a88"

    def setUp(self):
        super(TestAgentsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.agents_client = agents_client.AgentsClient(
            fake_auth, "network", "regionOne")

    def test_delete_agent(self):
        self.check_service_client_function(
            self.agents_client.delete_agent,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            agent_id=self.FAKE_AGENT_ID)
