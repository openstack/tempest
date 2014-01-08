# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest import exceptions
from tempest import test


class ServerAddressesNegativeTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ServerAddressesNegativeTestJSON, cls).setUpClass()
        cls.client = cls.servers_client

        resp, cls.server = cls.create_test_server(wait_until='ACTIVE')

    @test.attr(type=['negative', 'gate'])
    def test_list_server_addresses_invalid_server_id(self):
        # List addresses request should fail if server id not in system
        self.assertRaises(exceptions.NotFound, self.client.list_addresses,
                          '999')

    @test.attr(type=['negative', 'gate'])
    def test_list_server_addresses_by_network_neg(self):
        # List addresses by network should fail if network name not valid
        self.assertRaises(exceptions.NotFound,
                          self.client.list_addresses_by_network,
                          self.server['id'], 'invalid')


class ServerAddressesNegativeTestXML(ServerAddressesNegativeTestJSON):
    _interface = 'xml'
