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

import time

from tempest_lib.common.utils import misc
from tempest_lib import exceptions as lib_exc

from tempest import exceptions
from tempest.services.network.json import base


class NetworkClient(base.BaseNetworkClient):

    """Tempest REST client for Neutron.

    Uses v2 of the Neutron API, since the V1 API has been removed from the
    code base.

    Implements create, delete, update, list and show for the basic Neutron
    abstractions (networks, sub-networks, routers, ports and floating IP):

    Implements add/remove interface to router using subnet ID / port ID

    It also implements list, show, update and reset for OpenStack Networking
    quotas
    """

    def create_bulk_network(self, **kwargs):
        """create bulk network

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2.html#bulkCreateNetwork
        """
        uri = '/networks'
        return self.create_resource(uri, kwargs)

    def create_bulk_subnet(self, **kwargs):
        """create bulk subnet

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2.html#bulkCreateSubnet
        """
        uri = '/subnets'
        return self.create_resource(uri, kwargs)

    def create_bulk_port(self, **kwargs):
        """create bulk port

        Available params: see http://developer.openstack.org/
                              api-ref-networking-v2.html#bulkCreatePorts
        """
        uri = '/ports'
        return self.create_resource(uri, kwargs)

    def wait_for_resource_deletion(self, resource_type, id, client=None):
        """Waits for a resource to be deleted."""
        start_time = int(time.time())
        while True:
            if self.is_resource_deleted(resource_type, id, client=client):
                return
            if int(time.time()) - start_time >= self.build_timeout:
                raise exceptions.TimeoutException
            time.sleep(self.build_interval)

    def is_resource_deleted(self, resource_type, id, client=None):
        if client is None:
            client = self
        method = 'show_' + resource_type
        try:
            getattr(client, method)(id)
        except AttributeError:
            raise Exception("Unknown resource type %s " % resource_type)
        except lib_exc.NotFound:
            return True
        return False

    def wait_for_resource_status(self, fetch, status, interval=None,
                                 timeout=None):
        """Waits for a network resource to reach a status

        @param fetch: the callable to be used to query the resource status
        @type fecth: callable that takes no parameters and returns the resource
        @param status: the status that the resource has to reach
        @type status: String
        @param interval: the number of seconds to wait between each status
          query
        @type interval: Integer
        @param timeout: the maximum number of seconds to wait for the resource
          to reach the desired status
        @type timeout: Integer
        """
        if not interval:
            interval = self.build_interval
        if not timeout:
            timeout = self.build_timeout
        start_time = time.time()

        while time.time() - start_time <= timeout:
            resource = fetch()
            if resource['status'] == status:
                return
            time.sleep(interval)

        # At this point, the wait has timed out
        message = 'Resource %s' % (str(resource))
        message += ' failed to reach status %s' % status
        message += ' (current: %s)' % resource['status']
        message += ' within the required time %s' % timeout
        caller = misc.find_test_caller()
        if caller:
            message = '(%s) %s' % (caller, message)
        raise exceptions.TimeoutException(message)

    def create_router(self, name, admin_state_up=True, **kwargs):
        post_body = {'router': kwargs}
        post_body['router']['name'] = name
        post_body['router']['admin_state_up'] = admin_state_up
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

    def list_router_interfaces(self, uuid):
        uri = '/ports?device_id=%s' % uuid
        return self.list_resources(uri)

    def list_l3_agents_hosting_router(self, router_id):
        uri = '/routers/%s/l3-agents' % router_id
        return self.list_resources(uri)

    def list_dhcp_agent_hosting_network(self, network_id):
        uri = '/networks/%s/dhcp-agents' % network_id
        return self.list_resources(uri)

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
