# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
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

import netaddr
import testtools

from tempest.api.network import base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class RoutersTest(base.BaseNetworkTest):

    def _add_router_interface_with_subnet_id(self, router_id, subnet_id):
        interface = self.routers_client.add_router_interface(
            router_id, subnet_id=subnet_id)
        self.addCleanup(self._remove_router_interface_with_subnet_id,
                        router_id, subnet_id)
        self.assertEqual(subnet_id, interface['subnet_id'])
        return interface

    def _remove_router_interface_with_subnet_id(self, router_id, subnet_id):
        body = self.routers_client.remove_router_interface(router_id,
                                                           subnet_id=subnet_id)
        self.assertEqual(subnet_id, body['subnet_id'])

    @classmethod
    def skip_checks(cls):
        super(RoutersTest, cls).skip_checks()
        if not utils.is_extension_enabled('router', 'network'):
            msg = "router extension not enabled."
            raise cls.skipException(msg)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('f64403e2-8483-4b34-8ccd-b09a87bcc68c')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    def test_create_show_list_update_delete_router(self):
        # Create a router
        router_name = data_utils.rand_name(self.__class__.__name__ + '-router')
        router = self.create_router(
            router_name,
            admin_state_up=False,
            external_network_id=CONF.network.public_network_id)
        self.addCleanup(self.delete_router, router)
        self.assertEqual(router['name'], router_name)
        self.assertEqual(router['admin_state_up'], False)
        self.assertEqual(
            router['external_gateway_info']['network_id'],
            CONF.network.public_network_id)
        # Show details of the created router
        router_show = self.routers_client.show_router(
            router['id'])['router']
        self.assertEqual(router_show['name'], router['name'])
        self.assertEqual(
            router_show['external_gateway_info']['network_id'],
            CONF.network.public_network_id)
        # List routers and verify if created router is there in response
        routers = self.routers_client.list_routers()['routers']
        self.assertIn(router['id'], map(lambda x: x['id'], routers))
        # Update the name of router and verify if it is updated
        updated_name = 'updated' + router['name']
        router_update = self.routers_client.update_router(
            router['id'], name=updated_name)['router']
        self.assertEqual(router_update['name'], updated_name)
        router_show = self.routers_client.show_router(
            router['id'])['router']
        self.assertEqual(router_show['name'], updated_name)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('b42e6e39-2e37-49cc-a6f4-8467e940900a')
    def test_add_remove_router_interface_with_subnet_id(self):
        network_name = data_utils.rand_name(self.__class__.__name__)
        network = self.networks_client.create_network(
            name=network_name)['network']
        self.addCleanup(self.networks_client.delete_network,
                        network['id'])
        subnet = self.create_subnet(network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet['id'])
        router = self.create_router()
        self.addCleanup(self.delete_router, router)
        # Add router interface with subnet id
        interface = self.routers_client.add_router_interface(
            router['id'], subnet_id=subnet['id'])
        self.addCleanup(self._remove_router_interface_with_subnet_id,
                        router['id'], subnet['id'])
        self.assertIn('subnet_id', interface.keys())
        self.assertIn('port_id', interface.keys())
        # Verify router id is equal to device id in port details
        show_port_body = self.ports_client.show_port(
            interface['port_id'])
        self.assertEqual(show_port_body['port']['device_id'],
                         router['id'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('2b7d2f37-6748-4d78-92e5-1d590234f0d5')
    def test_add_remove_router_interface_with_port_id(self):
        network_name = data_utils.rand_name(self.__class__.__name__)
        network = self.networks_client.create_network(
            name=network_name)['network']
        self.addCleanup(self.networks_client.delete_network,
                        network['id'])
        subnet = self.create_subnet(network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet['id'])
        router = self.create_router()
        self.addCleanup(self.delete_router, router)
        port_body = self.ports_client.create_port(
            network_id=network['id'])
        # add router interface to port created above
        interface = self.routers_client.add_router_interface(
            router['id'],
            port_id=port_body['port']['id'])
        self.addCleanup(self.routers_client.remove_router_interface,
                        router['id'], port_id=port_body['port']['id'])
        self.assertIn('subnet_id', interface.keys())
        self.assertIn('port_id', interface.keys())
        # Verify router id is equal to device id in port details
        show_port_body = self.ports_client.show_port(
            interface['port_id'])
        self.assertEqual(show_port_body['port']['device_id'],
                         router['id'])

    @decorators.idempotent_id('cbe42f84-04c2-11e7-8adb-fa163e4fa634')
    @utils.requires_ext(extension='ext-gw-mode', service='network')
    @testtools.skipUnless(CONF.network.public_network_id,
                          'The public_network_id option must be specified.')
    @decorators.skip_because(bug='1676207')
    def test_create_router_set_gateway_with_fixed_ip(self):
        # Don't know public_network_address, so at first create address
        # from public_network and delete
        port = self.admin_ports_client.create_port(
            network_id=CONF.network.public_network_id)['port']
        self.admin_ports_client.delete_port(port_id=port['id'])

        fixed_ip = {
            'subnet_id': port['fixed_ips'][0]['subnet_id'],
            'ip_address': port['fixed_ips'][0]['ip_address']
        }
        external_gateway_info = {
            'network_id': CONF.network.public_network_id,
            'external_fixed_ips': [fixed_ip]
        }

        # Create a router and set gateway to fixed_ip
        router = self.admin_routers_client.create_router(
            external_gateway_info=external_gateway_info)['router']
        self.addCleanup(self.admin_routers_client.delete_router,
                        router_id=router['id'])
        # Examine router's gateway is equal to fixed_ip
        self.assertEqual(router['external_gateway_info'][
                         'external_fixed_ips'][0]['ip_address'],
                         fixed_ip['ip_address'])

    @decorators.idempotent_id('c86ac3a8-50bd-4b00-a6b8-62af84a0765c')
    @utils.requires_ext(extension='extraroute', service='network')
    def test_update_delete_extra_route(self):
        # Create different cidr for each subnet to avoid cidr duplicate
        # The cidr starts from project_cidr
        next_cidr = self.cidr
        # Prepare to build several routes
        test_routes = []
        routes_num = 4
        # Create a router
        router = self.create_router(admin_state_up=True)
        self.addCleanup(self.delete_router, router)
        self.addCleanup(
            self._delete_extra_routes,
            router['id'])
        # Update router extra route, second ip of the range is
        # used as next hop
        for i in range(routes_num):
            network_name = data_utils.rand_name(self.__class__.__name__)
            network = self.networks_client.create_network(
                name=network_name)['network']
            self.addCleanup(self.networks_client.delete_network,
                            network['id'])
            subnet = self.create_subnet(network, cidr=next_cidr)
            self.addCleanup(self.subnets_client.delete_subnet, subnet['id'])
            next_cidr = next_cidr.next()

            # Add router interface with subnet id
            self.create_router_interface(router['id'], subnet['id'])
            self.addCleanup(self._remove_router_interface_with_subnet_id,
                            router['id'], subnet['id'])
            cidr = netaddr.IPNetwork(subnet['cidr'])
            next_hop = str(cidr[2])
            destination = str(subnet['cidr'])
            test_routes.append(
                {'nexthop': next_hop, 'destination': destination}
            )

        test_routes.sort(key=lambda x: x['destination'])
        extra_route = self.routers_client.update_router(
            router['id'], routes=test_routes)
        show_body = self.routers_client.show_router(router['id'])
        # Assert the number of routes
        self.assertEqual(routes_num, len(extra_route['router']['routes']))
        self.assertEqual(routes_num, len(show_body['router']['routes']))

        routes = extra_route['router']['routes']
        routes.sort(key=lambda x: x['destination'])
        # Assert the nexthops & destination
        for i in range(routes_num):
            self.assertEqual(test_routes[i]['destination'],
                             routes[i]['destination'])
            self.assertEqual(test_routes[i]['nexthop'], routes[i]['nexthop'])

        routes = show_body['router']['routes']
        routes.sort(key=lambda x: x['destination'])
        for i in range(routes_num):
            self.assertEqual(test_routes[i]['destination'],
                             routes[i]['destination'])
            self.assertEqual(test_routes[i]['nexthop'], routes[i]['nexthop'])

        self._delete_extra_routes(router['id'])
        show_body_after_deletion = self.routers_client.show_router(
            router['id'])
        self.assertEmpty(show_body_after_deletion['router']['routes'])

    def _delete_extra_routes(self, router_id):
        self.routers_client.update_router(router_id, routes=None)

    @decorators.idempotent_id('a8902683-c788-4246-95c7-ad9c6d63a4d9')
    def test_update_router_admin_state(self):
        router = self.create_router()
        self.addCleanup(self.delete_router, router)
        self.assertFalse(router['admin_state_up'])
        # Update router admin state
        update_body = self.routers_client.update_router(router['id'],
                                                        admin_state_up=True)
        self.assertTrue(update_body['router']['admin_state_up'])
        show_body = self.routers_client.show_router(router['id'])
        self.assertTrue(show_body['router']['admin_state_up'])

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('802c73c9-c937-4cef-824b-2191e24a6aab')
    def test_add_multiple_router_interfaces(self):
        network_name = data_utils.rand_name(self.__class__.__name__)
        network01 = self.networks_client.create_network(
            name=network_name)['network']
        self.addCleanup(self.networks_client.delete_network,
                        network01['id'])
        network_name = data_utils.rand_name(self.__class__.__name__)
        network02 = self.networks_client.create_network(
            name=network_name)['network']
        self.addCleanup(self.networks_client.delete_network,
                        network02['id'])
        subnet01 = self.create_subnet(network01)
        self.addCleanup(self.subnets_client.delete_subnet, subnet01['id'])
        sub02_cidr = self.cidr.next()
        subnet02 = self.create_subnet(network02, cidr=sub02_cidr)
        self.addCleanup(self.subnets_client.delete_subnet, subnet02['id'])
        router = self.create_router()
        self.addCleanup(self.delete_router, router)
        interface01 = self._add_router_interface_with_subnet_id(router['id'],
                                                                subnet01['id'])
        self._verify_router_interface(router['id'], subnet01['id'],
                                      interface01['port_id'])
        interface02 = self._add_router_interface_with_subnet_id(router['id'],
                                                                subnet02['id'])
        self._verify_router_interface(router['id'], subnet02['id'],
                                      interface02['port_id'])

    @decorators.idempotent_id('96522edf-b4b5-45d9-8443-fa11c26e6eff')
    def test_router_interface_port_update_with_fixed_ip(self):
        network_name = data_utils.rand_name(self.__class__.__name__)
        network = self.networks_client.create_network(
            name=network_name)['network']
        self.addCleanup(self.networks_client.delete_network,
                        network['id'])
        subnet = self.create_subnet(network)
        self.addCleanup(self.subnets_client.delete_subnet, subnet['id'])
        router = self.create_router()
        self.addCleanup(self.delete_router, router)
        fixed_ip = [{'subnet_id': subnet['id']}]
        interface = self._add_router_interface_with_subnet_id(router['id'],
                                                              subnet['id'])
        self.assertIn('port_id', interface)
        self.assertIn('subnet_id', interface)
        port = self.ports_client.show_port(interface['port_id'])
        self.assertEqual(port['port']['id'], interface['port_id'])
        router_port = self.ports_client.update_port(port['port']['id'],
                                                    fixed_ips=fixed_ip)
        self.assertEqual(subnet['id'],
                         router_port['port']['fixed_ips'][0]['subnet_id'])

    def _verify_router_interface(self, router_id, subnet_id, port_id):
        show_port_body = self.ports_client.show_port(port_id)
        interface_port = show_port_body['port']
        self.assertEqual(router_id, interface_port['device_id'])
        self.assertEqual(subnet_id,
                         interface_port['fixed_ips'][0]['subnet_id'])


class RoutersIpV6Test(RoutersTest):
    _ip_version = 6
