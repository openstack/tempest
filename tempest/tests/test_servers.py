from nose.plugins.attrib import attr
from tempest import openstack
from tempest.common.utils.data_utils import rand_name
import base64
import unittest2 as unittest


class ServersTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.servers_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref

    @attr(type='smoke')
    def test_create_delete_server(self):
        meta = {'hello': 'world'}
        accessIPv4 = '1.1.1.1'
        accessIPv6 = '::babe:220.12.22.2'
        name = rand_name('server')
        file_contents = 'This is a test file.'
        personality = [{'path': '/etc/test.txt',
                       'contents': base64.b64encode(file_contents)}]
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 meta=meta,
                                                 accessIPv4=accessIPv4,
                                                 accessIPv6=accessIPv6,
                                                 personality=personality)
        #Check the initial response
        self.assertEqual(202, resp.status)
        self.assertTrue(server['id'] is not None)
        self.assertTrue(server['adminPass'] is not None)

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('1.1.1.1', server['accessIPv4'])
        self.assertEqual('::babe:220.12.22.2', server['accessIPv6'])
        self.assertEqual(name, server['name'])
        self.assertEqual(self.image_ref, server['image']['id'])
        self.assertEqual(str(self.flavor_ref), server['flavor']['id'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])
        self.assertEqual(204, resp.status)

    @attr(type='smoke')
    def test_create_server_with_admin_password(self):
        """
        If an admin password is provided on server creation, the server's root
        password should be set to that password.
        """

        name = rand_name('server')
        resp, server = self.client.create_server(name, self.image_ref,
                                                 self.flavor_ref,
                                                 adminPass='testpassword')

        #Verify the password is set correctly in the response
        self.assertEqual('testpassword', server['adminPass'])

        #Teardown
        self.client.delete_server(server['id'])

    @attr(type='smoke')
    def test_update_server_name(self):
        """The server name should be changed to the the provided value"""
        name = rand_name('server')
        resp, server = self.client.create_server(name, self.image_ref,
                                                 self.flavor_ref)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Update the server with a new name
        resp, server = self.client.update_server(server['id'], name='newname')
        self.assertEquals(200, resp.status)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the name of the server has changed
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('newname', server['name'])

        #Teardown
        self.client.delete_server(server['id'])

    @attr(type='smoke')
    def test_update_access_server_address(self):
        """
        The server's access addresses should reflect the provided values
        """
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
        self.client.delete_server(server['id'])
