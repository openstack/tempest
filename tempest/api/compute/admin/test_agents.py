# Copyright 2014 NEC Corporation.  All rights reserved.
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

from oslo_log import log
from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test

LOG = log.getLogger(__name__)


class AgentsAdminTestJSON(base.BaseV2ComputeAdminTest):
    """
    Tests Agents API
    """

    @classmethod
    def setup_clients(cls):
        super(AgentsAdminTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.agents_client

    def setUp(self):
        super(AgentsAdminTestJSON, self).setUp()
        params = self._param_helper(
            hypervisor='common', os='linux', architecture='x86_64',
            version='7.0', url='xxx://xxxx/xxx/xxx',
            md5hash='add6bb58e139be103324d04d82d8f545')
        body = self.client.create_agent(**params)
        self.agent_id = body['agent_id']

    def tearDown(self):
        try:
            self.client.delete_agent(self.agent_id)
        except lib_exc.NotFound:
            pass
        except Exception:
            LOG.exception('Exception raised deleting agent %s', self.agent_id)
        super(AgentsAdminTestJSON, self).tearDown()

    def _param_helper(self, **kwargs):
        rand_key = 'architecture'
        if rand_key in kwargs:
            # NOTE: The rand_name is for avoiding agent conflicts.
            # If you try to create an agent with the same hypervisor,
            # os and architecture as an exising agent, Nova will return
            # an HTTPConflict or HTTPServerError.
            kwargs[rand_key] = data_utils.rand_name(kwargs[rand_key])
        return kwargs

    @test.attr(type='gate')
    @test.idempotent_id('1fc6bdc8-0b6d-4cc7-9f30-9b04fabe5b90')
    def test_create_agent(self):
        # Create an agent.
        params = self._param_helper(
            hypervisor='kvm', os='win', architecture='x86',
            version='7.0', url='xxx://xxxx/xxx/xxx',
            md5hash='add6bb58e139be103324d04d82d8f545')
        body = self.client.create_agent(**params)
        self.addCleanup(self.client.delete_agent, body['agent_id'])
        for expected_item, value in params.items():
            self.assertEqual(value, body[expected_item])

    @test.attr(type='gate')
    @test.idempotent_id('dc9ffd51-1c50-4f0e-a820-ae6d2a568a9e')
    def test_update_agent(self):
        # Update an agent.
        params = self._param_helper(
            version='8.0', url='xxx://xxxx/xxx/xxx2',
            md5hash='add6bb58e139be103324d04d82d8f547')
        body = self.client.update_agent(self.agent_id, **params)
        for expected_item, value in params.items():
            self.assertEqual(value, body[expected_item])

    @test.attr(type='gate')
    @test.idempotent_id('470e0b89-386f-407b-91fd-819737d0b335')
    def test_delete_agent(self):
        # Delete an agent.
        self.client.delete_agent(self.agent_id)

        # Verify the list doesn't contain the deleted agent.
        agents = self.client.list_agents()
        self.assertNotIn(self.agent_id, map(lambda x: x['agent_id'], agents))

    @test.attr(type='gate')
    @test.idempotent_id('6a326c69-654b-438a-80a3-34bcc454e138')
    def test_list_agents(self):
        # List all agents.
        agents = self.client.list_agents()
        self.assertTrue(len(agents) > 0, 'Cannot get any agents.(%s)' % agents)
        self.assertIn(self.agent_id, map(lambda x: x['agent_id'], agents))

    @test.attr(type='gate')
    @test.idempotent_id('eabadde4-3cd7-4ec4-a4b5-5a936d2d4408')
    def test_list_agents_with_filter(self):
        # List the agent builds by the filter.
        params = self._param_helper(
            hypervisor='xen', os='linux', architecture='x86',
            version='7.0', url='xxx://xxxx/xxx/xxx1',
            md5hash='add6bb58e139be103324d04d82d8f546')
        agent_xen = self.client.create_agent(**params)
        self.addCleanup(self.client.delete_agent, agent_xen['agent_id'])

        agent_id_xen = agent_xen['agent_id']
        params_filter = {'hypervisor': agent_xen['hypervisor']}
        agents = self.client.list_agents(params_filter)
        self.assertTrue(len(agents) > 0, 'Cannot get any agents.(%s)' % agents)
        self.assertIn(agent_id_xen, map(lambda x: x['agent_id'], agents))
        self.assertNotIn(self.agent_id, map(lambda x: x['agent_id'], agents))
