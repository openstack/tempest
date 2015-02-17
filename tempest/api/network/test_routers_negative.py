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
from tempest_lib import exceptions as lib_exc

from tempest.api.network import base_routers as base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class RoutersNegativeTest(base.BaseRouterTest):

    @classmethod
    def resource_setup(cls):
        super(RoutersNegativeTest, cls).resource_setup()
        if not test.is_extension_enabled('router', 'network'):
            msg = "router extension not enabled."
            raise cls.skipException(msg)
        cls.router = cls.create_router(data_utils.rand_name('router-'))
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)
        cls.tenant_cidr = (CONF.network.tenant_network_cidr
                           if cls._ip_version == 4 else
                           CONF.network.tenant_network_v6_cidr)

    @test.attr(type=['negative', 'smoke'])
    def test_router_add_gateway_invalid_network_returns_404(self):
        self.assertRaises(lib_exc.NotFound,
                          self.client.update_router,
                          self.router['id'],
                          external_gateway_info={
                              'network_id': self.router['id']})

    @test.attr(type=['negative', 'smoke'])
    def test_router_add_gateway_net_not_external_returns_400(self):
        alt_network = self.create_network(
            network_name=data_utils.rand_name('router-negative-'))
        sub_cidr = netaddr.IPNetwork(self.tenant_cidr).next()
        self.create_subnet(alt_network, cidr=sub_cidr)
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_router,
                          self.router['id'],
                          external_gateway_info={
                              'network_id': alt_network['id']})

    @test.attr(type=['negative', 'smoke'])
    def test_add_router_interfaces_on_overlapping_subnets_returns_400(self):
        network01 = self.create_network(
            network_name=data_utils.rand_name('router-network01-'))
        network02 = self.create_network(
            network_name=data_utils.rand_name('router-network02-'))
        subnet01 = self.create_subnet(network01)
        subnet02 = self.create_subnet(network02)
        self._add_router_interface_with_subnet_id(self.router['id'],
                                                  subnet01['id'])
        self.assertRaises(lib_exc.BadRequest,
                          self._add_router_interface_with_subnet_id,
                          self.router['id'],
                          subnet02['id'])

    @test.attr(type=['negative', 'smoke'])
    def test_router_remove_interface_in_use_returns_409(self):
        self.client.add_router_interface_with_subnet_id(
            self.router['id'], self.subnet['id'])
        self.assertRaises(lib_exc.Conflict,
                          self.client.delete_router,
                          self.router['id'])

    @test.attr(type=['negative', 'smoke'])
    def test_show_non_existent_router_returns_404(self):
        router = data_utils.rand_name('non_exist_router')
        self.assertRaises(lib_exc.NotFound, self.client.show_router,
                          router)

    @test.attr(type=['negative', 'smoke'])
    def test_update_non_existent_router_returns_404(self):
        router = data_utils.rand_name('non_exist_router')
        self.assertRaises(lib_exc.NotFound, self.client.update_router,
                          router, name="new_name")

    @test.attr(type=['negative', 'smoke'])
    def test_delete_non_existent_router_returns_404(self):
        router = data_utils.rand_name('non_exist_router')
        self.assertRaises(lib_exc.NotFound, self.client.delete_router,
                          router)


class RoutersNegativeIpV6Test(RoutersNegativeTest):
    _ip_version = 6
