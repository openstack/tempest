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


class NetworksClient(base.BaseNetworkClient):

    def create_network(self, **kwargs):
        """Creates a network.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#create-network
        """
        uri = '/networks'
        post_data = {'network': kwargs}
        return self.create_resource(uri, post_data)

    def update_network(self, network_id, **kwargs):
        """Updates a network.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#update-network
        """
        uri = '/networks/%s' % network_id
        post_data = {'network': kwargs}
        return self.update_resource(uri, post_data)

    def show_network(self, network_id, **fields):
        """Shows details for a network.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-network-details
        """
        uri = '/networks/%s' % network_id
        return self.show_resource(uri, **fields)

    def delete_network(self, network_id):
        uri = '/networks/%s' % network_id
        return self.delete_resource(uri)

    def list_networks(self, **filters):
        """Lists networks to which the tenant has access.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-networks
        """
        uri = '/networks'
        return self.list_resources(uri, **filters)

    def create_bulk_networks(self, **kwargs):
        """Create multiple networks in a single request.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#bulk-create-networks
        """
        uri = '/networks'
        return self.create_resource(uri, kwargs)

    def list_dhcp_agents_on_hosting_network(self, network_id):
        uri = '/networks/%s/dhcp-agents' % network_id
        return self.list_resources(uri)
