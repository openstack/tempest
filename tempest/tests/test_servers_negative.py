import unittest2 as unittest
from tempest import openstack
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions


class ServersNegativeTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.servers_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref
        cls.ssh_timeout = cls.config.nova.ssh_timeout

    def test_server_name_blank(self):
        """Create a server with name parameter empty"""
        try:
            resp, server = self.client.create_server('', self.image_ref,
                                                     self.flavor_ref)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Server name cannot be blank')

    def test_personality_file_contents_not_encoded(self):
        """Use an unencoded file when creating a server with personality"""
        file_contents = 'This is a test file.'
        personality = [{'path': '/etc/testfile.txt',
                        'contents': file_contents}]

        try:
            resp, server = self.client.create_server('test',
                                                      self.image_ref,
                                                      self.flavor_ref,
                                                      personality=personality)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Unencoded file contents should not be accepted')

    def test_create_with_invalid_image(self):
        """Create a server with an unknown image"""
        try:
            resp, server = self.client.create_server('fail', -1,
                                                     self.flavor_ref)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Cannot create a server with an invalid image')

    def test_create_with_invalid_flavor(self):
        """Create a server with an unknown flavor"""
        try:
            self.client.create_server('fail', self.image_ref, -1)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Cannot create a server with an invalid flavor')

    @unittest.skip('Bug in Diablo, lp#891264')
    def test_invalid_access_ip_v4_address(self):
        """An access IPv4 address must match a valid address pattern"""
        accessIPv4 = '1.1.1.1.1.1'
        name = rand_name('server')
        try:
            resp, server = self.client.create_server(name,
                                                     self.image_ref,
                                                     self.flavor_ref,
                                                     accessIPv4=accessIPv4)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Access IPv4 address must match the correct format')

    @unittest.skip('Bug in Diablo, lp#891264')
    def test_invalid_ip_v6_address(self):
        """An access IPv6 address must match a valid address pattern"""
        accessIPv6 = 'notvalid'
        name = rand_name('server')
        try:
            resp, server = self.client.create_server(name,
                                                     self.image_ref,
                                                     self.flavor_ref,
                                                     accessIPv6=accessIPv6)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Access IPv6 address must match the correct format')
