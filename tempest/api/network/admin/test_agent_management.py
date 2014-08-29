# Copyright 2013 IBM Corp.
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

from tempest.api.network import base
from tempest.common import tempest_fixtures as fixtures
from tempest import test


class AgentManagementTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(AgentManagementTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('agent', 'network'):
            msg = "agent extension not enabled."
            raise cls.skipException(msg)
        resp, body = cls.admin_client.list_agents()
        agents = body['agents']
        cls.agent = agents[0]

    @test.attr(type='smoke')
    def test_list_agent(self):
        _, body = self.admin_client.list_agents()
        agents = body['agents']
        # Hearthbeats must be excluded from comparison
        self.agent.pop('heartbeat_timestamp', None)
        self.agent.pop('configurations', None)
        for agent in agents:
            agent.pop('heartbeat_timestamp', None)
            agent.pop('configurations', None)
        self.assertIn(self.agent, agents)

    @test.attr(type=['smoke'])
    def test_list_agents_non_admin(self):
        _, body = self.client.list_agents()
        self.assertEqual(len(body["agents"]), 0)

    @test.attr(type='smoke')
    def test_show_agent(self):
        _, body = self.admin_client.show_agent(self.agent['id'])
        agent = body['agent']
        self.assertEqual(agent['id'], self.agent['id'])

    @test.attr(type='smoke')
    def test_update_agent_status(self):
        origin_status = self.agent['admin_state_up']
        # Try to update the 'admin_state_up' to the original
        # one to avoid the negative effect.
        agent_status = {'admin_state_up': origin_status}
        _, body = self.admin_client.update_agent(agent_id=self.agent['id'],
                                                 agent_info=agent_status)
        updated_status = body['agent']['admin_state_up']
        self.assertEqual(origin_status, updated_status)

    @test.attr(type='smoke')
    def test_update_agent_description(self):
        self.useFixture(fixtures.LockFixture('agent_description'))
        description = 'description for update agent.'
        agent_description = {'description': description}
        _, body = self.admin_client.update_agent(agent_id=self.agent['id'],
                                                 agent_info=agent_description)
        self.addCleanup(self._restore_agent)
        updated_description = body['agent']['description']
        self.assertEqual(updated_description, description)

    def _restore_agent(self):
        """
        Restore the agent description after update test.
        """
        description = self.agent['description'] or ''
        origin_agent = {'description': description}
        self.admin_client.update_agent(agent_id=self.agent['id'],
                                       agent_info=origin_agent)


class AgentManagementTestXML(AgentManagementTestJSON):
    _interface = 'xml'
