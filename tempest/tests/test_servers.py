from nose.plugins.attrib import attr
from base_compute_test import BaseComputeTest
from tempest.common.utils.data_utils import rand_name


class ServersTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        cls.client = cls.servers_client

    @attr(type='smoke')
    def test_create_server_with_admin_password(self):
        """
        If an admin password is provided on server creation, the server's root
        password should be set to that password.
        """

        try:
            name = rand_name('server')
            resp, server = self.client.create_server(name, self.image_ref,
                                                 self.flavor_ref,
                                                 adminPass='testpassword')

            #Verify the password is set correctly in the response
            self.assertEqual('testpassword', server['adminPass'])

        #Teardown
        finally:
            self.client.delete_server(server['id'])

    def test_create_with_existing_server_name(self):
        """Creating a server with a name that already exists is allowed"""

        try:
            server_name = rand_name('server')
            resp, server = self.client.create_server(server_name,
                                                    self.image_ref,
                                                    self.flavor_ref)
            self.client.wait_for_server_status(server['id'], 'ACTIVE')
            id1 = server['id']
            resp, server = self.client.create_server(server_name,
                                                    self.image_ref,
                                                    self.flavor_ref)
            self.client.wait_for_server_status(server['id'], 'ACTIVE')
            id2 = server['id']
            self.assertNotEqual(id1, id2, "Did not create a new server")
            resp, server = self.client.get_server(id1)
            name1 = server['name']
            resp, server = self.client.get_server(id2)
            name2 = server['name']
            self.assertEqual(name1, name2)
        finally:
            for server_id in (id1, id2):
                if server_id:
                    self.client.delete_server(server_id)

    @attr(type='smoke')
    def test_create_specify_keypair(self):
        """Specify a keypair while creating a server"""

        try:
            key_name = rand_name('key')
            resp, keypair = self.keypairs_client.create_keypair(key_name)
            resp, body = self.keypairs_client.list_keypairs()
            server_name = rand_name('server')
            resp, server = self.client.create_server(server_name,
                                                    self.image_ref,
                                                    self.flavor_ref,
                                                    key_name=key_name)
            self.assertEqual('202', resp['status'])
            self.client.wait_for_server_status(server['id'], 'ACTIVE')
            resp, server = self.client.get_server(server['id'])
            self.assertEqual(key_name, server['key_name'])
        finally:
            if server:
                self.client.delete_server(server['id'])

    @attr(type='smoke')
    def test_update_server_name(self):
        """The server name should be changed to the the provided value"""
        try:
            name = rand_name('server')
            resp, server = self.client.create_server(name, self.image_ref,
                                                 self.flavor_ref)
            self.client.wait_for_server_status(server['id'], 'ACTIVE')

            #Update the server with a new name
            resp, server = self.client.update_server(server['id'],
                                                 name='newname')
            self.assertEquals(200, resp.status)
            self.client.wait_for_server_status(server['id'], 'ACTIVE')

            #Verify the name of the server has changed
            resp, server = self.client.get_server(server['id'])
            self.assertEqual('newname', server['name'])

        #Teardown
        finally:
            self.client.delete_server(server['id'])

    @attr(type='smoke')
    def test_update_access_server_address(self):
        """
        The server's access addresses should reflect the provided values
        """
        try:
            name = rand_name('server')
            resp, server = self.client.create_server(name, self.image_ref,
                                                 self.flavor_ref)
            self.client.wait_for_server_status(server['id'], 'ACTIVE')

            #Update the IPv4 and IPv6 access addresses
            resp, body = self.client.update_server(server['id'],
                                               accessIPv4='1.1.1.1',
                                               accessIPv6='::babe:2.2.2.2')
            self.assertEqual(200, resp.status)
            self.client.wait_for_server_status(server['id'], 'ACTIVE')

            #Verify the access addresses have been updated
            resp, server = self.client.get_server(server['id'])
            self.assertEqual('1.1.1.1', server['accessIPv4'])
            self.assertEqual('::babe:2.2.2.2', server['accessIPv6'])

        #Teardown
        finally:
            self.client.delete_server(server['id'])

    def test_delete_server_while_in_building_state(self):
        """Delete a server while it's VM state is Building"""
        name = rand_name('server')
        resp, server = self.client.create_server(name, self.image_ref,
                                                self.flavor_ref)
        self.client.wait_for_server_status(server['id'], 'BUILD')
        resp, _ = self.client.delete_server(server['id'])
        self.assertEqual('204', resp['status'])
