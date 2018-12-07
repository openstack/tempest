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
from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class AgentManagementTestJSON(base.BaseAdminNetworkTest):

    @classmethod
    def skip_checks(cls):
        super(AgentManagementTestJSON, cls).skip_checks()
        if not utils.is_extension_enabled('agent', 'network'):
            msg = "agent extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        super(AgentManagementTestJSON, cls).resource_setup()
        body = cls.admin_agents_client.list_agents()
        agents = body['agents']
        cls.agent = agents[0]

    @decorators.idempotent_id('9c80f04d-11f3-44a4-8738-ed2f879b0ff4')
    def test_list_agent(self):
        body = self.admin_agents_client.list_agents()
        agents = body['agents']
        # Hearthbeats must be excluded from comparison
        self.agent.pop('heartbeat_timestamp', None)
        self.agent.pop('configurations', None)
        for agent in agents:
            agent.pop('heartbeat_timestamp', None)
            agent.pop('configurations', None)
        self.assertIn(self.agent, agents)

    @decorators.idempotent_id('869bc8e8-0fda-4a30-9b71-f8a7cf58ca9f')
    def test_show_agent(self):
        body = self.admin_agents_client.show_agent(self.agent['id'])
        agent = body['agent']
        self.assertEqual(agent['id'], self.agent['id'])

    @decorators.idempotent_id('371dfc5b-55b9-4cb5-ac82-c40eadaac941')
    def test_update_agent_status(self):
        origin_status = self.agent['admin_state_up']
        # Try to update the 'admin_state_up' to the original
        # one to avoid the negative effect.
        agent_status = {'admin_state_up': origin_status}
        body = self.admin_agents_client.update_agent(agent_id=self.agent['id'],
                                                     agent=agent_status)
        updated_status = body['agent']['admin_state_up']
        self.assertEqual(origin_status, updated_status)

    @decorators.idempotent_id('68a94a14-1243-46e6-83bf-157627e31556')
    def test_update_agent_description(self):
        self.useFixture(fixtures.LockFixture('agent_description'))
        description = 'description for update agent.'
        agent_description = {'description': description}
        body = self.admin_agents_client.update_agent(agent_id=self.agent['id'],
                                                     agent=agent_description)
        self.addCleanup(self._restore_agent)
        updated_description = body['agent']['description']
        self.assertEqual(updated_description, description)

    def _restore_agent(self):
        """Restore the agent description after update test"""

        description = self.agent['description'] or ''
        origin_agent = {'description': description}
        self.admin_agents_client.update_agent(agent_id=self.agent['id'],
                                              agent=origin_agent)

    @decorators.idempotent_id('b33af888-b6ac-4e68-a0ca-0444c2696cf9')
    @decorators.attr(type=['negative'])
    def test_delete_agent_negative(self):
        non_existent_id = data_utils.rand_uuid()
        self.assertRaises(
            lib_exc.NotFound,
            self.admin_agents_client.delete_agent, non_existent_id)
