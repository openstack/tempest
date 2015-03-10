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

from tempest_lib.common.utils import data_utils

from tempest.api.compute import base
from tempest import test


class ServersTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(ServersTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    def tearDown(self):
        self.clear_servers()
        super(ServersTestJSON, self).tearDown()

    @test.attr(type='gate')
    @test.idempotent_id('b92d5ec7-b1dd-44a2-87e4-45e888c46ef0')
    def test_create_server_with_admin_password(self):
        # If an admin password is provided on server creation, the server's
        # root password should be set to that password.
        server = self.create_test_server(adminPass='testpassword')

        # Verify the password is set correctly in the response
        self.assertEqual('testpassword', server['adminPass'])

    @test.attr(type='gate')
    @test.idempotent_id('8fea6be7-065e-47cf-89b8-496e6f96c699')
    def test_create_with_existing_server_name(self):
        # Creating a server with a name that already exists is allowed

        # TODO(sdague): clear out try, we do cleanup one layer up
        server_name = data_utils.rand_name('server')
        server = self.create_test_server(name=server_name,
                                         wait_until='ACTIVE')
        id1 = server['id']
        server = self.create_test_server(name=server_name,
                                         wait_until='ACTIVE')
        id2 = server['id']
        self.assertNotEqual(id1, id2, "Did not create a new server")
        server = self.client.get_server(id1)
        name1 = server['name']
        server = self.client.get_server(id2)
        name2 = server['name']
        self.assertEqual(name1, name2)

    @test.attr(type='gate')
    @test.idempotent_id('f9e15296-d7f9-4e62-b53f-a04e89160833')
    def test_create_specify_keypair(self):
        # Specify a keypair while creating a server

        key_name = data_utils.rand_name('key')
        self.keypairs_client.create_keypair(key_name)
        self.keypairs_client.list_keypairs()
        server = self.create_test_server(key_name=key_name)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')
        server = self.client.get_server(server['id'])
        self.assertEqual(key_name, server['key_name'])

    def _update_server_name(self, server_id, status):
        # The server name should be changed to the the provided value
        new_name = data_utils.rand_name('server')
        # Update the server with a new name
        self.client.update_server(server_id,
                                  name=new_name)
        self.client.wait_for_server_status(server_id, status)

        # Verify the name of the server has changed
        server = self.client.get_server(server_id)
        self.assertEqual(new_name, server['name'])
        return server

    @test.attr(type='gate')
    @test.idempotent_id('5e6ccff8-349d-4852-a8b3-055df7988dd2')
    def test_update_server_name(self):
        # The server name should be changed to the the provided value
        server = self.create_test_server(wait_until='ACTIVE')

        self._update_server_name(server['id'], 'ACTIVE')

    @test.attr(type='gate')
    @test.idempotent_id('6ac19cb1-27a3-40ec-b350-810bdc04c08e')
    def test_update_server_name_in_stop_state(self):
        # The server name should be changed to the the provided value
        server = self.create_test_server(wait_until='ACTIVE')
        self.client.stop(server['id'])
        self.client.wait_for_server_status(server['id'], 'SHUTOFF')
        updated_server = self._update_server_name(server['id'], 'SHUTOFF')
        self.assertNotIn('progress', updated_server)

    @test.attr(type='gate')
    @test.idempotent_id('89b90870-bc13-4b73-96af-f9d4f2b70077')
    def test_update_access_server_address(self):
        # The server's access addresses should reflect the provided values
        server = self.create_test_server(wait_until='ACTIVE')

        # Update the IPv4 and IPv6 access addresses
        self.client.update_server(server['id'],
                                  accessIPv4='1.1.1.1',
                                  accessIPv6='::babe:202:202')
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        # Verify the access addresses have been updated
        server = self.client.get_server(server['id'])
        self.assertEqual('1.1.1.1', server['accessIPv4'])
        self.assertEqual('::babe:202:202', server['accessIPv6'])

    @test.attr(type='gate')
    @test.idempotent_id('38fb1d02-c3c5-41de-91d3-9bc2025a75eb')
    def test_create_server_with_ipv6_addr_only(self):
        # Create a server without an IPv4 address(only IPv6 address).
        server = self.create_test_server(accessIPv6='2001:2001::3')
        self.client.wait_for_server_status(server['id'], 'ACTIVE')
        server = self.client.get_server(server['id'])
        self.assertEqual('2001:2001::3', server['accessIPv6'])
