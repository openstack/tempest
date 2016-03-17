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

    def _update_router(self, router_id, set_enable_snat, **kwargs):
        uri = '/routers/%s' % router_id
        body = self.show_resource(uri)
        update_body = {}
        update_body['name'] = kwargs.get('name', body['router']['name'])
        update_body['admin_state_up'] = kwargs.get(
            'admin_state_up', body['router']['admin_state_up'])
        cur_gw_info = body['router']['external_gateway_info']
        if cur_gw_info:
            # TODO(kevinbenton): setting the external gateway info is not
            # allowed for a regular tenant. If the ability to update is also
            # merged, a test case for this will need to be added similar to
            # the SNAT case.
            cur_gw_info.pop('external_fixed_ips', None)
            if not set_enable_snat:
                cur_gw_info.pop('enable_snat', None)
        update_body['external_gateway_info'] = kwargs.get(
            'external_gateway_info', body['router']['external_gateway_info'])
        if 'distributed' in kwargs:
            update_body['distributed'] = kwargs['distributed']
        update_body = dict(router=update_body)
        return self.update_resource(uri, update_body)

    def update_router(self, router_id, **kwargs):
        """Update a router leaving enable_snat to its default value."""
        # If external_gateway_info contains enable_snat the request will fail
        # with 404 unless executed with admin client, and therefore we instruct
        # _update_router to not set this attribute
        # NOTE(salv-orlando): The above applies as long as Neutron's default
        # policy is to restrict enable_snat usage to admins only.
        return self._update_router(router_id, set_enable_snat=False, **kwargs)

    def show_router(self, router_id, **fields):
        uri = '/routers/%s' % router_id
        return self.show_resource(uri, **fields)

    def delete_router(self, router_id):
        uri = '/routers/%s' % router_id
        return self.delete_resource(uri)

    def list_routers(self, **filters):
        uri = '/routers'
        return self.list_resources(uri, **filters)

    def update_extra_routes(self, router_id, **kwargs):
        """Update Extra routes.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#updateExtraRoutes
        """
        uri = '/routers/%s' % router_id
        put_body = {'router': kwargs}
        return self.update_resource(uri, put_body)

    def delete_extra_routes(self, router_id):
        uri = '/routers/%s' % router_id
        put_body = {
            'router': {
                'routes': None
            }
        }
        return self.update_resource(uri, put_body)

    def update_router_with_snat_gw_info(self, router_id, **kwargs):
        """Update a router passing also the enable_snat attribute.

        This method must be execute with admin credentials, otherwise the API
        call will return a 404 error.
        """
        return self._update_router(router_id, set_enable_snat=True, **kwargs)

    def add_router_interface(self, router_id, **kwargs):
        """Add router interface.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#addRouterInterface
        """
        uri = '/routers/%s/add_router_interface' % router_id
        return self.update_resource(uri, kwargs)

    def remove_router_interface(self, router_id, **kwargs):
        """Remove router interface.

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2-ext.html#removeRouterInterface
        """
        uri = '/routers/%s/remove_router_interface' % router_id
        return self.update_resource(uri, kwargs)

    def list_l3_agents_hosting_router(self, router_id):
        uri = '/routers/%s/l3-agents' % router_id
        return self.list_resources(uri)
