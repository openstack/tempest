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

from tempest.api.compute import base
from tempest import test


class ServerAddressesTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_credentials(cls):
        # This test module might use a network and a subnet
        cls.set_network_resources(network=True, subnet=True)
        super(ServerAddressesTestJSON, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(ServerAddressesTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServerAddressesTestJSON, cls).resource_setup()

        cls.server = cls.create_test_server(wait_until='ACTIVE')

    @test.attr(type='smoke')
    @test.idempotent_id('6eb718c0-02d9-4d5e-acd1-4e0c269cef39')
    @test.services('network')
    def test_list_server_addresses(self):
        # All public and private addresses for
        # a server should be returned

        addresses = self.client.list_addresses(self.server['id'])

        # We do not know the exact network configuration, but an instance
        # should at least have a single public or private address
        self.assertTrue(len(addresses) >= 1)
        for network_name, network_addresses in addresses.iteritems():
            self.assertTrue(len(network_addresses) >= 1)
            for address in network_addresses:
                self.assertTrue(address['addr'])
                self.assertTrue(address['version'])

    @test.attr(type='smoke')
    @test.idempotent_id('87bbc374-5538-4f64-b673-2b0e4443cc30')
    @test.services('network')
    def test_list_server_addresses_by_network(self):
        # Providing a network type should filter
        # the addresses return by that type

        addresses = self.client.list_addresses(self.server['id'])

        # Once again we don't know the environment's exact network config,
        # but the response for each individual network should be the same
        # as the partial result of the full address list
        id = self.server['id']
        for addr_type in addresses:
            addr = self.client.list_addresses_by_network(id, addr_type)

            addr = addr[addr_type]
            for address in addresses[addr_type]:
                self.assertTrue(any([a for a in addr if a == address]))
