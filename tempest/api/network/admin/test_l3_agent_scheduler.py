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


class L3AgentSchedulerJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        List routers that the given L3 agent is hosting.
        List L3 agents hosting the given router.

    v2.0 of the Neutron API is assumed. It is also assumed that the following
    options are defined in the [network] section of etc/tempest.conf:
    """

    @classmethod
    def setUpClass(cls):
        super(L3AgentSchedulerJSON, cls).setUpClass()
        if not test.is_extension_enabled('l3_agent_scheduler', 'network'):
            msg = "L3 Agent Scheduler Extension not enabled."
            raise cls.skipException(msg)

    @test.attr(type='smoke')
    def test_list_routers_on_l3_agent(self):
        resp, body = self.admin_client.list_agents()
        agents = body['agents']
        for a in agents:
            if a['agent_type'] == 'L3 agent':
                agent = a
        resp, body = self.admin_client.list_routers_on_l3_agent(
            agent['id'])
        self.assertEqual('200', resp['status'])

    @test.attr(type='smoke')
    def test_list_l3_agents_hosting_router(self):
        name = data_utils.rand_name('router-')
        resp, router = self.client.create_router(name)
        self.assertEqual('201', resp['status'])
        resp, body = self.admin_client.list_l3_agents_hosting_router(
            router['router']['id'])
        self.assertEqual('200', resp['status'])
        resp, _ = self.client.delete_router(router['router']['id'])
        self.assertEqual(204, resp.status)


class L3AgentSchedulerXML(L3AgentSchedulerJSON):
    _interface = 'xml'
