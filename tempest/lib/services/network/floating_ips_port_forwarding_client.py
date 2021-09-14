# Copyright 2021 Red Hat, Inc.
# All rights reserved.
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


class FloatingIpsPortForwardingClient(base.BaseNetworkClient):

    def create_port_forwarding(self, floatingip_id, **kwargs):
        """Creates a floating IP port forwarding.

        Creates port forwarding by using the configuration that you define in
        the request object.
        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#create-port-forwarding
        """
        uri = '/floatingips/%s/port_forwardings' % floatingip_id
        post_data = {'port_forwarding': kwargs}
        return self.create_resource(uri, post_data)

    def update_port_forwarding(
            self, floatingip_id, port_forwarding_id, **kwargs):
        """Updates a floating IP port_forwarding resource.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#update-a-port-forwarding
        """
        uri = '/floatingips/%s/port_forwardings/%s' % (
            floatingip_id, port_forwarding_id)
        post_data = {'port_forwarding': kwargs}
        return self.update_resource(uri, post_data)

    def show_port_forwarding(
            self, floatingip_id, port_forwarding_id, **fields):
        """Shows details for a floating IP port forwarding id.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#show-port-forwarding
        """
        uri = '/floatingips/%s/port_forwardings/%s' % (
            floatingip_id, port_forwarding_id)
        return self.show_resource(uri, **fields)

    def delete_port_forwarding(self, floatingip_id, port_forwarding_id):
        """Deletes a floating IP port_forwarding resource.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#delete-a-floating-ip-port-forwarding
        """
        uri = '/floatingips/%s/port_forwardings/%s' % (
            floatingip_id, port_forwarding_id)
        return self.delete_resource(uri)

    def list_port_forwardings(self, floatingip_id, **filters):
        """Lists floating Ip port forwardings.

        For a full list of available parameters, please refer to the official
        API reference:
        https://docs.openstack.org/api-ref/network/v2/index.html#list-floating-ip-port-forwardings-detail
        """
        uri = '/floatingips/%s/port_forwardings' % floatingip_id
        return self.list_resources(uri, **filters)
