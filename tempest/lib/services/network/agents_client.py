# Copyright 2015 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.network import base


class AgentsClient(base.BaseNetworkClient):

    def update_agent(self, agent_id, **kwargs):
        """Update an agent.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/#update-agent
        """
        uri = '/agents/%s' % agent_id
        return self.update_resource(uri, kwargs)

    def show_agent(self, agent_id, **fields):
        """Show details for an agent.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/#show-agent-details
        """
        uri = '/agents/%s' % agent_id
        return self.show_resource(uri, **fields)

    def list_agents(self, **filters):
        """List all agents.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/#list-all-agents
        """
        uri = '/agents'
        return self.list_resources(uri, **filters)

    def list_routers_on_l3_agent(self, agent_id):
        """List routers that an l3 agent hosts.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/#list-routers-hosted-by-an-l3-agent
        """
        uri = '/agents/%s/l3-routers' % agent_id
        return self.list_resources(uri)

    def create_router_on_l3_agent(self, agent_id, **kwargs):
        """Add a router to an l3 agent.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/#schedule-router-to-an-l3-agent
        """
        uri = '/agents/%s/l3-routers' % agent_id
        return self.create_resource(uri, kwargs, expect_empty_body=True)

    def delete_router_from_l3_agent(self, agent_id, router_id):
        """Remove a router to an l3 agent.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/#remove-l3-router-from-an-l3-agent
        """
        uri = '/agents/%s/l3-routers/%s' % (agent_id, router_id)
        return self.delete_resource(uri)

    def list_networks_hosted_by_one_dhcp_agent(self, agent_id):
        uri = '/agents/%s/dhcp-networks' % agent_id
        return self.list_resources(uri)

    def delete_network_from_dhcp_agent(self, agent_id, network_id):
        uri = '/agents/%s/dhcp-networks/%s' % (agent_id,
                                               network_id)
        return self.delete_resource(uri)

    def add_dhcp_agent_to_network(self, agent_id, **kwargs):
        """Schedule a network to a DHCP agent.

        For a full list of available parameters, please refer to the official
        API reference:
        https://developer.openstack.org/api-ref/network/v2/#schedule-a-network-to-a-dhcp-agent
        """
        uri = '/agents/%s/dhcp-networks' % agent_id
        return self.create_resource(uri, kwargs, expect_empty_body=True)
