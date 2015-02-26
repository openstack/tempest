# Copyright 2012 OpenStack Foundation
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

from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class ServerAddressesNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_credentials(cls):
        cls.set_network_resources(network=True, subnet=True)
        super(ServerAddressesNegativeTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServerAddressesNegativeTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServerAddressesNegativeTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(wait_until='ACTIVE')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('02c3f645-2d2e-4417-8525-68c0407d001b')
    @test.services('network')
    def test_list_server_addresses_invalid_server_id(self):
        # List addresses request should fail if server id not in system
        self.assertRaises(lib_exc.NotFound, self.client.list_addresses,
                          '999')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('a2ab5144-78c0-4942-a0ed-cc8edccfd9ba')
    @test.services('network')
    def test_list_server_addresses_by_network_neg(self):
        # List addresses by network should fail if network name not valid
        self.assertRaises(lib_exc.NotFound,
                          self.client.list_addresses_by_network,
                          self.server['id'], 'invalid')
