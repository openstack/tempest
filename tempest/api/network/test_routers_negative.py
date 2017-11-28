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

from tempest.api.network import base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class RoutersNegativeTest(base.BaseNetworkTest):

    @classmethod
    def skip_checks(cls):
        super(RoutersNegativeTest, cls).skip_checks()
        if not utils.is_extension_enabled('router', 'network'):
            msg = "router extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        super(RoutersNegativeTest, cls).resource_setup()
        cls.router = cls.create_router()
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('37a94fc0-a834-45b9-bd23-9a81d2fd1e22')
    def test_router_add_gateway_invalid_network_returns_404(self):
        self.assertRaises(lib_exc.NotFound,
                          self.routers_client.update_router,
                          self.router['id'],
                          external_gateway_info={
                              'network_id': self.router['id']})

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('11836a18-0b15-4327-a50b-f0d9dc66bddd')
    def test_router_add_gateway_net_not_external_returns_400(self):
        alt_network = self.create_network()
        sub_cidr = self.cidr.next()
        self.create_subnet(alt_network, cidr=sub_cidr)
        self.assertRaises(lib_exc.BadRequest,
                          self.routers_client.update_router,
                          self.router['id'],
                          external_gateway_info={
                              'network_id': alt_network['id']})

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('957751a3-3c68-4fa2-93b6-eb52ea10db6e')
    def test_add_router_interfaces_on_overlapping_subnets_returns_400(self):
        network01 = self.create_network(
            network_name=data_utils.rand_name('router-network01-'))
        network02 = self.create_network(
            network_name=data_utils.rand_name('router-network02-'))
        subnet01 = self.create_subnet(network01)
        subnet02 = self.create_subnet(network02)
        interface = self.routers_client.add_router_interface(
            self.router['id'], subnet_id=subnet01['id'])
        self.addCleanup(self.routers_client.remove_router_interface,
                        self.router['id'], subnet_id=subnet01['id'])
        self.assertEqual(subnet01['id'], interface['subnet_id'])
        self.assertRaises(lib_exc.BadRequest,
                          self.routers_client.add_router_interface,
                          self.router['id'],
                          subnet_id=subnet02['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('04df80f9-224d-47f5-837a-bf23e33d1c20')
    def test_router_remove_interface_in_use_returns_409(self):
        self.routers_client.add_router_interface(self.router['id'],
                                                 subnet_id=self.subnet['id'])
        self.addCleanup(self.routers_client.remove_router_interface,
                        self.router['id'], subnet_id=self.subnet['id'])
        self.assertRaises(lib_exc.Conflict,
                          self.routers_client.delete_router,
                          self.router['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c2a70d72-8826-43a7-8208-0209e6360c47')
    def test_show_non_existent_router_returns_404(self):
        router = data_utils.rand_name('non_exist_router')
        self.assertRaises(lib_exc.NotFound, self.routers_client.show_router,
                          router)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b23d1569-8b0c-4169-8d4b-6abd34fad5c7')
    def test_update_non_existent_router_returns_404(self):
        router = data_utils.rand_name('non_exist_router')
        self.assertRaises(lib_exc.NotFound, self.routers_client.update_router,
                          router, name="new_name")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c7edc5ad-d09d-41e6-a344-5c0c31e2e3e4')
    def test_delete_non_existent_router_returns_404(self):
        router = data_utils.rand_name('non_exist_router')
        self.assertRaises(lib_exc.NotFound, self.routers_client.delete_router,
                          router)


class RoutersNegativeIpV6Test(RoutersNegativeTest):
    _ip_version = 6


class DvrRoutersNegativeTest(base.BaseNetworkTest):

    @classmethod
    def skip_checks(cls):
        super(DvrRoutersNegativeTest, cls).skip_checks()
        if not utils.is_extension_enabled('dvr', 'network'):
            msg = "DVR extension not enabled."
            raise cls.skipException(msg)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('4990b055-8fc7-48ab-bba7-aa28beaad0b9')
    def test_router_create_tenant_distributed_returns_forbidden(self):
        self.assertRaises(lib_exc.Forbidden, self.create_router,
                          distributed=True)
