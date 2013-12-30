# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.test import attr


class AgentManagementTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(AgentManagementTestJSON, cls).setUpClass()
        resp, body = cls.admin_client.list_agents()
        agents = body['agents']
        cls.agent = agents[0]

    @attr(type='smoke')
    def test_list_agent(self):
        resp, body = self.admin_client.list_agents()
        self.assertEqual('200', resp['status'])
        agents = body['agents']
        self.assertIn(self.agent, agents)

    @attr(type=['smoke'])
    def test_list_agents_non_admin(self):
        resp, body = self.client.list_agents()
        self.assertEqual('200', resp['status'])
        self.assertEqual(len(body["agents"]), 0)

    @attr(type='smoke')
    def test_show_agent(self):
        resp, body = self.admin_client.show_agent(self.agent['id'])
        agent = body['agent']
        self.assertEqual('200', resp['status'])
        self.assertEqual(agent['id'], self.agent['id'])

    @attr(type='smoke')
    def test_update_agent_status(self):
        origin_status = self.agent['admin_state_up']
        # Try to update the 'admin_state_up' to the original
        # one to avoid the negative effect.
        agent_status = {'admin_state_up': origin_status}
        resp, body = self.admin_client.update_agent(agent_id=self.agent['id'],
                                                    agent_info=agent_status)
        updated_status = body['agent']['admin_state_up']
        self.assertEqual('200', resp['status'])
        self.assertEqual(origin_status, updated_status)

    @attr(type='smoke')
    def test_update_agent_description(self):
        self.useFixture(fixtures.LockFixture('agent_description'))
        description = 'description for update agent.'
        agent_description = {'description': description}
        resp, body = self.admin_client.update_agent(
            agent_id=self.agent['id'],
            agent_info=agent_description)
        self.assertEqual('200', resp['status'])
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
