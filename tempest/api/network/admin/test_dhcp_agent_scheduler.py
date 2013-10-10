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
from tempest.test import attr


class DHCPAgentSchedulersTestJSON(base.BaseAdminNetworkTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(DHCPAgentSchedulersTestJSON, cls).setUpClass()
        # Create a network and make sure it will be hosted by a
        # dhcp agent.
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.cidr = cls.subnet['cidr']
        cls.port = cls.create_port(cls.network)

    @attr(type='smoke')
    def test_list_dhcp_agent_hosting_network(self):
        resp, body = self.admin_client.list_dhcp_agent_hosting_network(
            self.network['id'])
        self.assertEqual(resp['status'], '200')

    @attr(type='smoke')
    def test_list_networks_hosted_by_one_dhcp(self):
        resp, body = self.admin_client.list_dhcp_agent_hosting_network(
            self.network['id'])
        agents = body['agents']
        self.assertIsNotNone(agents)
        agent = agents[0]
        self.assertTrue(self._check_network_in_dhcp_agent(
            self.network['id'], agent))

    def _check_network_in_dhcp_agent(self, network_id, agent):
        network_ids = []
        resp, body = self.admin_client.list_networks_hosted_by_one_dhcp_agent(
            agent['id'])
        self.assertEqual(resp['status'], '200')
        networks = body['networks']
        for network in networks:
            network_ids.append(network['id'])
        return network_id in network_ids

    @attr(type='smoke')
    def test_remove_network_from_dhcp_agent(self):
        resp, body = self.admin_client.list_dhcp_agent_hosting_network(
            self.network['id'])
        agents = body['agents']
        self.assertIsNotNone(agents)
        # Get an agent.
        agent = agents[0]
        network_id = self.network['id']
        resp, body = self.admin_client.remove_network_from_dhcp_agent(
            agent_id=agent['id'],
            network_id=network_id)
        self.assertEqual(resp['status'], '204')
        self.assertFalse(self._check_network_in_dhcp_agent(
            network_id, agent))


class DHCPAgentSchedulersTestXML(DHCPAgentSchedulersTestJSON):
    _interface = 'xml'
