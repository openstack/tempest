from nose.plugins.attrib import attr
from tempest import openstack
from base_compute_test import BaseComputeTest
from tempest.common.utils.data_utils import rand_name
import base64


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
