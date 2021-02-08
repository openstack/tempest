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


class TrunksClient(base.BaseNetworkClient):

    def create_trunk(self, **kwargs):
        """Creates a trunk.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#create-trunk
        """
        uri = '/trunks'
        post_data = {'trunk': kwargs}
        return self.create_resource(uri, post_data)

    def update_trunk(self, trunk_id, **kwargs):
        """Updates a trunk.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#update-trunk
        """
        uri = '/trunks/%s' % trunk_id
        put_data = {'trunk': kwargs}
        return self.update_resource(uri, put_data)

    def show_trunk(self, trunk_id):
        """Shows details for a trunk.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-trunk
        """
        uri = '/trunks/%s' % trunk_id
        return self.show_resource(uri)

    def delete_trunk(self, trunk_id):
        """Deletes a trunk.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#delete-trunk
        """
        uri = '/trunks/%s' % trunk_id
        return self.delete_resource(uri)

    def list_trunks(self, **filters):
        """Lists trunks to which the tenant has access.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-trunks
        """
        uri = '/trunks'
        return self.list_resources(uri, **filters)

    def add_subports_to_trunk(self, trunk_id, sub_ports):
        """Add subports to a trunk.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#add-subports-to-trunk
        """
        uri = '/trunks/%s/add_subports' % trunk_id
        put_data = {'sub_ports': sub_ports}
        return self.update_resource(uri, put_data)

    def delete_subports_from_trunk(self, trunk_id, sub_ports):
        """Deletes subports from a trunk.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#delete-subports-from-trunk
        """
        uri = '/trunks/%s/remove_subports' % trunk_id
        put_data = {'sub_ports': sub_ports}
        return self.update_resource(uri, put_data)

    def list_subports_of_trunk(self, trunk_id):
        """List subports of a trunk.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-subports-for-trunk
        """
        uri = '/trunks/%s/get_subports' % trunk_id
        return self.list_resources(uri)
