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
        """Update agent."""
        # TODO(piyush): Current api-site doesn't contain this API description.
        # After fixing the api-site, we need to fix here also for putting the
        # link to api-site.
        # LP: https://bugs.launchpad.net/openstack-api-site/+bug/1526673
        uri = '/agents/%s' % agent_id
        return self.update_resource(uri, kwargs)

    def show_agent(self, agent_id, **fields):
        uri = '/agents/%s' % agent_id
        return self.show_resource(uri, **fields)

    def list_agents(self, **filters):
        uri = '/agents'
        return self.list_resources(uri, **filters)

    def list_routers_on_l3_agent(self, agent_id):
        uri = '/agents/%s/l3-routers' % agent_id
        return self.list_resources(uri)

    def create_router_on_l3_agent(self, agent_id, **kwargs):
        # TODO(piyush): Current api-site doesn't contain this API description.
        # After fixing the api-site, we need to fix here also for putting the
        # link to api-site.
        # LP: https://bugs.launchpad.net/openstack-api-site/+bug/1526670
        uri = '/agents/%s/l3-routers' % agent_id
        return self.create_resource(uri, kwargs)

    def delete_router_from_l3_agent(self, agent_id, router_id):
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
        # TODO(piyush): Current api-site doesn't contain this API description.
        # After fixing the api-site, we need to fix here also for putting the
        # link to api-site.
        # LP: https://bugs.launchpad.net/openstack-api-site/+bug/1526212
        uri = '/agents/%s/dhcp-networks' % agent_id
        return self.create_resource(uri, kwargs)
