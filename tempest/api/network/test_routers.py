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

from tempest.api.network import base_routers as base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class RoutersTest(base.BaseRouterTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(RoutersTest, cls).setUpClass()

    @test.attr(type='smoke')
    def test_create_show_list_update_delete_router(self):
        # Create a router
        # NOTE(salv-orlando): Do not invoke self.create_router
        # as we need to check the response code
        name = data_utils.rand_name('router-')
        resp, create_body = self.client.create_router(
            name, external_gateway_info={
                "network_id": CONF.network.public_network_id},
            admin_state_up=False)
        self.assertEqual('201', resp['status'])
        self.addCleanup(self._delete_router, create_body['router']['id'])
        self.assertEqual(create_body['router']['name'], name)
        self.assertEqual(
            create_body['router']['external_gateway_info']['network_id'],
            CONF.network.public_network_id)
        self.assertEqual(create_body['router']['admin_state_up'], False)
        # Show details of the created router
        resp, show_body = self.client.show_router(
            create_body['router']['id'])
        self.assertEqual('200', resp['status'])
        self.assertEqual(show_body['router']['name'], name)
        self.assertEqual(
            show_body['router']['external_gateway_info']['network_id'],
            CONF.network.public_network_id)
        self.assertEqual(show_body['router']['admin_state_up'], False)
        # List routers and verify if created router is there in response
        resp, list_body = self.client.list_routers()
        self.assertEqual('200', resp['status'])
        routers_list = list()
        for router in list_body['routers']:
            routers_list.append(router['id'])
        self.assertIn(create_body['router']['id'], routers_list)
        # Update the name of router and verify if it is updated
        updated_name = 'updated ' + name
        resp, update_body = self.client.update_router(
            create_body['router']['id'], name=updated_name)
        self.assertEqual('200', resp['status'])
        self.assertEqual(update_body['router']['name'], updated_name)
        resp, show_body = self.client.show_router(
            create_body['router']['id'])
        self.assertEqual(show_body['router']['name'], updated_name)

    @test.attr(type='smoke')
    def test_add_remove_router_interface_with_subnet_id(self):
        network = self.create_network()
        subnet = self.create_subnet(network)
        router = self.create_router(data_utils.rand_name('router-'))
        # Add router interface with subnet id
        resp, interface = self.client.add_router_interface_with_subnet_id(
            router['id'], subnet['id'])
        self.assertEqual('200', resp['status'])
        self.addCleanup(self._remove_router_interface_with_subnet_id,
                        router['id'], subnet['id'])
        self.assertIn('subnet_id', interface.keys())
        self.assertIn('port_id', interface.keys())
        # Verify router id is equal to device id in port details
        resp, show_port_body = self.client.show_port(
            interface['port_id'])
        self.assertEqual(show_port_body['port']['device_id'],
                         router['id'])

    @test.attr(type='smoke')
    def test_add_remove_router_interface_with_port_id(self):
        network = self.create_network()
        self.create_subnet(network)
        router = self.create_router(data_utils.rand_name('router-'))
        resp, port_body = self.client.create_port(
            network_id=network['id'])
        # add router interface to port created above
        resp, interface = self.client.add_router_interface_with_port_id(
            router['id'], port_body['port']['id'])
        self.assertEqual('200', resp['status'])
        self.addCleanup(self._remove_router_interface_with_port_id,
                        router['id'], port_body['port']['id'])
        self.assertIn('subnet_id', interface.keys())
        self.assertIn('port_id', interface.keys())
        # Verify router id is equal to device id in port details
        resp, show_port_body = self.client.show_port(
            interface['port_id'])
        self.assertEqual(show_port_body['port']['device_id'],
                         router['id'])

    def _verify_router_gateway(self, router_id, exp_ext_gw_info=None):
        resp, show_body = self.client.show_router(router_id)
        self.assertEqual('200', resp['status'])
        actual_ext_gw_info = show_body['router']['external_gateway_info']
        if exp_ext_gw_info is None:
            self.assertIsNone(actual_ext_gw_info)
            return
        # Verify only keys passed in exp_ext_gw_info
        for k, v in exp_ext_gw_info.iteritems():
            self.assertEqual(v, actual_ext_gw_info[k])

    def _verify_gateway_port(self, router_id):
        resp, list_body = self.admin_client.list_ports(
            network_id=CONF.network.public_network_id,
            device_id=router_id)
        self.assertEqual(len(list_body['ports']), 1)
        gw_port = list_body['ports'][0]
        fixed_ips = gw_port['fixed_ips']
        self.assertEqual(len(fixed_ips), 1)
        resp, public_net_body = self.admin_client.show_network(
            CONF.network.public_network_id)
        public_subnet_id = public_net_body['network']['subnets'][0]
        self.assertEqual(fixed_ips[0]['subnet_id'], public_subnet_id)

    @test.attr(type='smoke')
    def test_update_router_set_gateway(self):
        router = self.create_router(data_utils.rand_name('router-'))
        self.client.update_router(
            router['id'],
            external_gateway_info={
                'network_id': CONF.network.public_network_id})
        # Verify operation - router
        resp, show_body = self.client.show_router(router['id'])
        self.assertEqual('200', resp['status'])
        self._verify_router_gateway(
            router['id'],
            {'network_id': CONF.network.public_network_id})
        self._verify_gateway_port(router['id'])

    @test.requires_ext(extension='ext-gw-mode', service='network')
    @test.attr(type='smoke')
    def test_update_router_set_gateway_with_snat_explicit(self):
        router = self.create_router(data_utils.rand_name('router-'))
        self.admin_client.update_router_with_snat_gw_info(
            router['id'],
            external_gateway_info={
                'network_id': CONF.network.public_network_id,
                'enable_snat': True})
        self._verify_router_gateway(
            router['id'],
            {'network_id': CONF.network.public_network_id,
             'enable_snat': True})
        self._verify_gateway_port(router['id'])

    @test.requires_ext(extension='ext-gw-mode', service='network')
    @test.attr(type='smoke')
    def test_update_router_set_gateway_without_snat(self):
        router = self.create_router(data_utils.rand_name('router-'))
        self.admin_client.update_router_with_snat_gw_info(
            router['id'],
            external_gateway_info={
                'network_id': CONF.network.public_network_id,
                'enable_snat': False})
        self._verify_router_gateway(
            router['id'],
            {'network_id': CONF.network.public_network_id,
             'enable_snat': False})
        self._verify_gateway_port(router['id'])

    @test.attr(type='smoke')
    def test_update_router_unset_gateway(self):
        router = self.create_router(
            data_utils.rand_name('router-'),
            external_network_id=CONF.network.public_network_id)
        self.client.update_router(router['id'], external_gateway_info={})
        self._verify_router_gateway(router['id'])
        # No gateway port expected
        resp, list_body = self.admin_client.list_ports(
            network_id=CONF.network.public_network_id,
            device_id=router['id'])
        self.assertFalse(list_body['ports'])

    @test.requires_ext(extension='ext-gw-mode', service='network')
    @test.attr(type='smoke')
    def test_update_router_reset_gateway_without_snat(self):
        router = self.create_router(
            data_utils.rand_name('router-'),
            external_network_id=CONF.network.public_network_id)
        self.admin_client.update_router_with_snat_gw_info(
            router['id'],
            external_gateway_info={
                'network_id': CONF.network.public_network_id,
                'enable_snat': False})
        self._verify_router_gateway(
            router['id'],
            {'network_id': CONF.network.public_network_id,
             'enable_snat': False})
        self._verify_gateway_port(router['id'])

    @test.requires_ext(extension='extraroute', service='network')
    @test.attr(type='smoke')
    def test_update_extra_route(self):
        self.network = self.create_network()
        self.name = self.network['name']
        self.subnet = self.create_subnet(self.network)
        # Add router interface with subnet id
        self.router = self.create_router(data_utils.rand_name('router-'), True)
        self.create_router_interface(self.router['id'], self.subnet['id'])
        self.addCleanup(
            self._delete_extra_routes,
            self.router['id'])
        # Update router extra route
        cidr = netaddr.IPNetwork(self.subnet['cidr'])
        resp, extra_route = self.client.update_extra_routes(
            self.router['id'], str(cidr[0]), str(self.subnet['cidr']))

    def _delete_extra_routes(self, router_id):
        resp, _ = self.client.delete_extra_routes(router_id)
