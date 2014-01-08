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
from tempest.common.utils import data_utils
from tempest import test


class ServersV3TestJSON(base.BaseV3ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ServersV3TestJSON, cls).setUpClass()
        cls.client = cls.servers_client

    def tearDown(self):
        self.clear_servers()
        super(ServersV3TestJSON, self).tearDown()

    @test.attr(type='gate')
    def test_create_server_with_admin_password(self):
        # If an admin password is provided on server creation, the server's
        # root password should be set to that password.
        resp, server = self.create_test_server(admin_password='testpassword')

        # Verify the password is set correctly in the response
        self.assertEqual('testpassword', server['admin_password'])

    @test.attr(type='gate')
    def test_create_with_existing_server_name(self):
        # Creating a server with a name that already exists is allowed

        # TODO(sdague): clear out try, we do cleanup one layer up
        server_name = data_utils.rand_name('server')
        resp, server = self.create_test_server(name=server_name,
                                               wait_until='ACTIVE')
        id1 = server['id']
        resp, server = self.create_test_server(name=server_name,
                                               wait_until='ACTIVE')
        id2 = server['id']
        self.assertNotEqual(id1, id2, "Did not create a new server")
        resp, server = self.client.get_server(id1)
        name1 = server['name']
        resp, server = self.client.get_server(id2)
        name2 = server['name']
        self.assertEqual(name1, name2)

    @test.attr(type='gate')
    def test_create_specify_keypair(self):
        # Specify a keypair while creating a server

        key_name = data_utils.rand_name('key')
        resp, keypair = self.keypairs_client.create_keypair(key_name)
        resp, body = self.keypairs_client.list_keypairs()
        resp, server = self.create_test_server(key_name=key_name)
        self.assertEqual('202', resp['status'])
        self.client.wait_for_server_status(server['id'], 'ACTIVE')
        resp, server = self.client.get_server(server['id'])
        self.assertEqual(key_name, server['key_name'])

    @test.attr(type='gate')
    def test_update_server_name(self):
        # The server name should be changed to the the provided value
        resp, server = self.create_test_server(wait_until='ACTIVE')

        # Update the server with a new name
        resp, server = self.client.update_server(server['id'],
                                                 name='newname')
        self.assertEqual(200, resp.status)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        # Verify the name of the server has changed
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('newname', server['name'])

    @test.attr(type='gate')
    def test_update_access_server_address(self):
        # The server's access addresses should reflect the provided values
        resp, server = self.create_test_server(wait_until='ACTIVE')

        # Update the IPv4 and IPv6 access addresses
        resp, body = self.client.update_server(server['id'],
                                               access_ip_v4='1.1.1.1',
                                               access_ip_v6='::babe:202:202')
        self.assertEqual(200, resp.status)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        # Verify the access addresses have been updated
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('1.1.1.1', server['os-access-ips:access_ip_v4'])
        self.assertEqual('::babe:202:202',
                         server['os-access-ips:access_ip_v6'])

    @test.attr(type='gate')
    def test_delete_server_while_in_building_state(self):
        # Delete a server while it's VM state is Building
        resp, server = self.create_test_server(wait_until='BUILD')
        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='gate')
    def test_delete_active_server(self):
        # Delete a server while it's VM state is Active
        resp, server = self.create_test_server(wait_until='ACTIVE')
        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])

    @test.attr(type='gate')
    def test_create_server_with_ipv6_addr_only(self):
        # Create a server without an IPv4 address(only IPv6 address).
        resp, server = self.create_test_server(access_ip_v6='2001:2001::3')
        self.assertEqual('202', resp['status'])
        self.client.wait_for_server_status(server['id'], 'ACTIVE')
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('2001:2001::3', server['os-access-ips:access_ip_v6'])


class ServersV3TestXML(ServersV3TestJSON):
    _interface = 'xml'
