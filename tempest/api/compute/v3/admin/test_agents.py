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
from tempest import test


class AgentsAdminV3Test(base.BaseV3ComputeAdminTest):

    """
    Tests Agents API that require admin privileges
    """

    @classmethod
    def setUpClass(cls):
        super(AgentsAdminV3Test, cls).setUpClass()
        cls.client = cls.agents_admin_client

    @test.attr(type='gate')
    def test_create_update_list_delete_agents(self):

        """
        1. Create 2 agents.
        2. Update one of the agents.
        3. List all agent builds.
        4. List the agent builds by the filter.
        5. Delete agents.
        """
        params_kvm = expected_kvm = {'hypervisor': 'kvm',
                                     'os': 'win',
                                     'architecture': 'x86',
                                     'version': '7.0',
                                     'url': 'xxx://xxxx/xxx/xxx',
                                     'md5hash': ("""add6bb58e139be103324d04d"""
                                                 """82d8f545""")}

        resp, agent_kvm = self.client.create_agent(**params_kvm)
        self.assertEqual(201, resp.status)
        for expected_item, value in expected_kvm.items():
            self.assertEqual(value, agent_kvm[expected_item])

        params_xen = expected_xen = {'hypervisor': 'xen',
                                     'os': 'linux',
                                     'architecture': 'x86',
                                     'version': '7.0',
                                     'url': 'xxx://xxxx/xxx/xxx1',
                                     'md5hash': """add6bb58e139be103324d04d8"""
                                                """2d8f546"""}

        resp, agent_xen = self.client.create_agent(**params_xen)
        self.assertEqual(201, resp.status)

        for expected_item, value in expected_xen.items():
            self.assertEqual(value, agent_xen[expected_item])

        params_kvm_new = expected_kvm_new = {'version': '8.0',
                                             'url': 'xxx://xxxx/xxx/xxx2',
                                             'md5hash': """add6bb58e139be103"""
                                                        """324d04d82d8f547"""}

        resp, resp_agent_kvm = self.client.update_agent(agent_kvm['agent_id'],
                                                        **params_kvm_new)
        self.assertEqual(200, resp.status)
        for expected_item, value in expected_kvm_new.items():
            self.assertEqual(value, resp_agent_kvm[expected_item])

        resp, agents = self.client.list_agents()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(agents) > 1)

        params_filter = {'hypervisor': 'kvm'}
        resp, agent = self.client.list_agents(params_filter)
        self.assertEqual(200, resp.status)
        self.assertTrue(len(agent) > 0)
        self.assertEqual('kvm', agent[0]['hypervisor'])

        resp, _ = self.client.delete_agent(agent_kvm['agent_id'])
        self.assertEqual(204, resp.status)
        resp, _ = self.client.delete_agent(agent_xen['agent_id'])
        self.assertEqual(204, resp.status)
