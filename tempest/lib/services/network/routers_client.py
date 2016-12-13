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


class RoutersClient(base.BaseNetworkClient):

    def create_router(self, **kwargs):
        """Create a router.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#createRouter
        """
        post_body = {'router': kwargs}
        uri = '/routers'
        return self.create_resource(uri, post_body)

    def update_router(self, router_id, **kwargs):
        """Updates a logical router.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#updateRouter
        """
        uri = '/routers/%s' % router_id
        update_body = {'router': kwargs}
        return self.update_resource(uri, update_body)

    def show_router(self, router_id, **fields):
        """Shows details for a router.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#showRouter
        """
        uri = '/routers/%s' % router_id
        return self.show_resource(uri, **fields)

    def delete_router(self, router_id):
        uri = '/routers/%s' % router_id
        return self.delete_resource(uri)

    def list_routers(self, **filters):
        """Lists logical routers.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#listRouters
        """
        uri = '/routers'
        return self.list_resources(uri, **filters)

    def add_router_interface(self, router_id, **kwargs):
        """Add router interface.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#
                              addRouterInterface
        """
        uri = '/routers/%s/add_router_interface' % router_id
        return self.update_resource(uri, kwargs)

    def remove_router_interface(self, router_id, **kwargs):
        """Remove router interface.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#
                              deleteRouterInterface
        """
        uri = '/routers/%s/remove_router_interface' % router_id
        return self.update_resource(uri, kwargs)

    def list_l3_agents_hosting_router(self, router_id):
        uri = '/routers/%s/l3-agents' % router_id
        return self.list_resources(uri)
