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

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.openstack.common import log
from tempest import test

LOG = log.getLogger(__name__)


class AgentsAdminTestJSON(base.BaseV2ComputeAdminTest):
    """
    Tests Agents API
    """

    @classmethod
    def setUpClass(cls):
        super(AgentsAdminTestJSON, cls).setUpClass()
        cls.client = cls.os_adm.agents_client

    def setUp(self):
        super(AgentsAdminTestJSON, self).setUp()
        params = self._param_helper(
            hypervisor='common', os='linux', architecture='x86_64',
            version='7.0', url='xxx://xxxx/xxx/xxx',
            md5hash='add6bb58e139be103324d04d82d8f545')
        resp, body = self.client.create_agent(**params)
        self.assertEqual(200, resp.status)
        self.agent_id = body['agent_id']

    def tearDown(self):
        try:
            self.client.delete_agent(self.agent_id)
        except exceptions.NotFound:
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
    def test_create_agent(self):
        # Create an agent.
        params = self._param_helper(
            hypervisor='kvm', os='win', architecture='x86',
            version='7.0', url='xxx://xxxx/xxx/xxx',
            md5hash='add6bb58e139be103324d04d82d8f545')
        resp, body = self.client.create_agent(**params)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.delete_agent, body['agent_id'])
        for expected_item, value in params.items():
            self.assertEqual(value, body[expected_item])

    @test.attr(type='gate')
    def test_update_agent(self):
        # Update an agent.
        params = self._param_helper(
            version='8.0', url='xxx://xxxx/xxx/xxx2',
            md5hash='add6bb58e139be103324d04d82d8f547')
        resp, body = self.client.update_agent(self.agent_id, **params)
        self.assertEqual(200, resp.status)
        for expected_item, value in params.items():
            self.assertEqual(value, body[expected_item])

    @test.attr(type='gate')
    def test_delete_agent(self):
        # Delete an agent.
        resp, _ = self.client.delete_agent(self.agent_id)
        self.assertEqual(200, resp.status)

        # Verify the list doesn't contain the deleted agent.
        resp, agents = self.client.list_agents()
        self.assertEqual(200, resp.status)
        self.assertNotIn(self.agent_id, map(lambda x: x['agent_id'], agents))

    @test.attr(type='gate')
    def test_list_agents(self):
        # List all agents.
        resp, agents = self.client.list_agents()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(agents) > 0, 'Cannot get any agents.(%s)' % agents)
        self.assertIn(self.agent_id, map(lambda x: x['agent_id'], agents))

    @test.attr(type='gate')
    def test_list_agents_with_filter(self):
        # List the agent builds by the filter.
        params = self._param_helper(
            hypervisor='xen', os='linux', architecture='x86',
            version='7.0', url='xxx://xxxx/xxx/xxx1',
            md5hash='add6bb58e139be103324d04d82d8f546')
        resp, agent_xen = self.client.create_agent(**params)
        self.assertEqual(200, resp.status)
        self.addCleanup(self.client.delete_agent, agent_xen['agent_id'])

        agent_id_xen = agent_xen['agent_id']
        params_filter = {'hypervisor': agent_xen['hypervisor']}
        resp, agents = self.client.list_agents(params_filter)
        self.assertEqual(200, resp.status)
        self.assertTrue(len(agents) > 0, 'Cannot get any agents.(%s)' % agents)
        self.assertIn(agent_id_xen, map(lambda x: x['agent_id'], agents))
        self.assertNotIn(self.agent_id, map(lambda x: x['agent_id'], agents))
