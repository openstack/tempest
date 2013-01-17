# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from nose.plugins.attrib import attr

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.tests.compute.base import BaseCompTest


class ServerAddressesTest(BaseCompTest):

    @classmethod
    def setUpClass(cls):
        super(ServerAddressesTest, cls).setUpClass()
        cls.client = cls.servers_client

        cls.name = rand_name('server')
        resp, cls.server = cls.client.create_server(cls.name,
                                                    cls.image_ref,
                                                    cls.flavor_ref)
        cls.client.wait_for_server_status(cls.server['id'], 'ACTIVE')

    @classmethod
    def tearDownClass(cls):
        cls.client.delete_server(cls.server['id'])
        super(ServerAddressesTest, cls).tearDownClass()

    @attr(type='negative', category='server-addresses')
    def test_list_server_addresses_invalid_server_id(self):
        # List addresses request should fail if server id not in system

        try:
            self.client.list_addresses('999')
        except exceptions.NotFound:
            pass
        else:
            self.fail('The server rebuild for a non existing server should not'
                      ' be allowed')

    @attr(type='negative', category='server-addresses')
    def test_list_server_addresses_by_network_neg(self):
        # List addresses by network should fail if network name not valid

        try:
            self.client.list_addresses_by_network(self.server['id'], 'invalid')
        except exceptions.NotFound:
            pass
        else:
            self.fail('The server rebuild for a non existing server should not'
                      ' be allowed')

    @attr(type='smoke', category='server-addresses')
    def test_list_server_addresses(self):
        # All public and private addresses for
        # a server should be returned

        resp, addresses = self.client.list_addresses(self.server['id'])
        self.assertEqual('200', resp['status'])

        # We do not know the exact network configuration, but an instance
        # should at least have a single public or private address
        self.assertGreaterEqual(len(addresses), 1)
        for network_name, network_addresses in addresses.iteritems():
            self.assertGreaterEqual(len(network_addresses), 1)
            for address in network_addresses:
                self.assertTrue(address['addr'])
                self.assertTrue(address['version'])

    @attr(type='smoke', category='server-addresses')
    def test_list_server_addresses_by_network(self):
        # Providing a network type should filter
        # the addresses return by that type

        resp, addresses = self.client.list_addresses(self.server['id'])

        # Once again we don't know the environment's exact network config,
        # but the response for each individual network should be the same
        # as the partial result of the full address list
        id = self.server['id']
        for addr_type in addresses:
            resp, addr = self.client.list_addresses_by_network(id, addr_type)
            self.assertEqual('200', resp['status'])

            addr = addr[addr_type]
            for address in addresses[addr_type]:
                self.assertTrue(any([a for a in addr if a == address]))
