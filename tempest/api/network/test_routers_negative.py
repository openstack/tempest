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

from tempest.api.network import base_routers as base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class RoutersNegativeTest(base.BaseRouterTest):
    _interface = 'json'

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(RoutersNegativeTest, cls).setUpClass()
        if not test.is_extension_enabled('router', 'network'):
            msg = "router extension not enabled."
            raise cls.skipException(msg)
        cls.router = cls.create_router(data_utils.rand_name('router-'))
        cls.network = cls.create_network()
        cls.subnet = cls.create_subnet(cls.network)

    @test.attr(type=['negative', 'smoke'])
    def test_router_add_gateway_invalid_network_returns_404(self):
        self.assertRaises(exceptions.NotFound,
                          self.client.update_router,
                          self.router['id'],
                          external_gateway_info={
                              'network_id': self.router['id']})

    @test.attr(type=['negative', 'smoke'])
    def test_router_add_gateway_net_not_external_returns_400(self):
        self.create_subnet(self.network)
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_router,
                          self.router['id'],
                          external_gateway_info={
                              'network_id': self.network['id']})

    @test.attr(type=['negative', 'smoke'])
    def test_router_remove_interface_in_use_returns_409(self):
        self.client.add_router_interface_with_subnet_id(
            self.router['id'], self.subnet['id'])
        self.assertRaises(exceptions.Conflict,
                          self.client.delete_router,
                          self.router['id'])
