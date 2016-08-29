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


class FloatingIPsClient(base.BaseNetworkClient):

    def create_floatingip(self, **kwargs):
        """Creates a floating IP.

        If you specify port information, associates the floating IP with an
        internal port.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#createFloatingIp
        """
        uri = '/floatingips'
        post_data = {'floatingip': kwargs}
        return self.create_resource(uri, post_data)

    def update_floatingip(self, floatingip_id, **kwargs):
        """Updates a floating IP and its association with an internal port.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#updateFloatingIp
        """
        uri = '/floatingips/%s' % floatingip_id
        post_data = {'floatingip': kwargs}
        return self.update_resource(uri, post_data)

    def show_floatingip(self, floatingip_id, **fields):
        """Shows details for a floating IP.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#showFloatingIp
        """
        uri = '/floatingips/%s' % floatingip_id
        return self.show_resource(uri, **fields)

    def delete_floatingip(self, floatingip_id):
        uri = '/floatingips/%s' % floatingip_id
        return self.delete_resource(uri)

    def list_floatingips(self, **filters):
        """Lists floating IPs.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#listFloatingIps
        """
        uri = '/floatingips'
        return self.list_resources(uri, **filters)
