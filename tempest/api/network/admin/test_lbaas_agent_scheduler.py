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
from tempest.common.utils import data_utils
from tempest import test


class LBaaSAgentSchedulerTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        List pools the given LBaaS agent is hosting.
        Show a LBaaS agent hosting the given pool.

    v2.0 of the Neutron API is assumed. It is also assumed that the following
    options are defined in the [networki-feature-enabled] section of
    etc/tempest.conf:

        api_extensions
    """

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(LBaaSAgentSchedulerTestJSON, cls).setUpClass()
        if not test.is_extension_enabled('lbaas_agent_scheduler', 'network'):
            msg = "LBaaS Agent Scheduler Extension not enabled."
            raise cls.skipException(msg)
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        pool_name = data_utils.rand_name('pool-')
        cls.pool = cls.create_pool(pool_name, "ROUND_ROBIN",
                                   "HTTP", cls.subnet)

    @test.attr(type='smoke')
    def test_list_pools_on_lbaas_agent(self):
        found = False
        resp, body = self.admin_client.list_agents(
            agent_type="Loadbalancer agent")
        self.assertEqual('200', resp['status'])
        agents = body['agents']
        for a in agents:
            msg = 'Load Balancer agent expected'
            self.assertEqual(a['agent_type'], 'Loadbalancer agent', msg)
            resp, body = (
                self.admin_client.list_pools_hosted_by_one_lbaas_agent(
                    a['id']))
            self.assertEqual('200', resp['status'])
            pools = body['pools']
            if self.pool['id'] in [p['id'] for p in pools]:
                found = True
        msg = 'Unable to find Load Balancer agent hosting pool'
        self.assertTrue(found, msg)

    @test.attr(type='smoke')
    def test_show_lbaas_agent_hosting_pool(self):
        resp, body = self.admin_client.show_lbaas_agent_hosting_pool(
            self.pool['id'])
        self.assertEqual('200', resp['status'])
        self.assertEqual('Loadbalancer agent', body['agent']['agent_type'])


class LBaaSAgentSchedulerTestXML(LBaaSAgentSchedulerTestJSON):
    _interface = 'xml'
