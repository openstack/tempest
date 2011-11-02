from nose.plugins.attrib import attr
from storm import openstack
import unittest2 as unittest
import storm.config
from storm.common.utils.data_utils import rand_name


class ServerActionsTest(unittest.TestCase):
    resize_available = storm.config.StormConfig().env.resize_available

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.servers_client
        cls.config = storm.config.StormConfig()
        cls.image_ref = cls.config.env.image_ref
        cls.image_ref_alt = cls.config.env.image_ref_alt
        cls.flavor_ref = cls.config.env.flavor_ref
        cls.flavor_ref_alt = cls.config.env.flavor_ref_alt

    def setUp(self):
        self.name = rand_name('server')
        resp, server = self.client.create_server(self.name, self.image_ref,
                                                 self.flavor_ref)
        self.id = server['id']
        self.client.wait_for_server_status(self.id, 'ACTIVE')

    def tearDown(self):
        self.client.delete_server(self.id)

    @attr(type='smoke')
    def test_change_server_password(self):
        """ The server's password should be set to the provided password """
        resp, body = self.client.change_password(self.id, 'newpass')
        self.client.wait_for_server_status(self.id, 'ACTIVE')
        #TODO: SSH in to verify the new password works

    @attr(type='smoke')
    def test_reboot_server_hard(self):
        """ The server should be power cycled """
        #TODO: Add validation the server has been rebooted

        resp, body = self.client.reboot(self.id, 'HARD')
        self.client.wait_for_server_status(self.id, 'ACTIVE')

    @attr(type='smoke')
    def test_reboot_server_soft(self):
        """ The server should be signaled to reboot gracefully """
        #TODO: Add validation the server has been rebooted

        resp, body = self.client.reboot(self.id, 'SOFT')
        self.client.wait_for_server_status(self.id, 'ACTIVE')

    @attr(type='smoke')
    def test_rebuild_server(self):
        """ The server should be rebuilt using the provided image """

        self.client.rebuild(self.id, self.image_ref_alt, name='rebuiltserver')
        self.client.wait_for_server_status(self.id, 'ACTIVE')
        resp, server = self.client.get_server(self.id)
        self.assertEqual(self.image_ref_alt, server['image']['id'])
        self.assertEqual('rebuiltserver', server['name'])

    @attr(type='smoke')
    @unittest.skipIf(not resize_available, 'Resize not available.')
    def test_resize_server_confirm(self):
        """
        The server's RAM and disk space should be modified to that of
        the provided flavor
        """

        self.client.resize(self.id, self.flavor_ref_alt)
        self.client.wait_for_server_status(self.id, 'VERIFY_RESIZE')

        self.client.confirm_resize(self.id)
        self.client.wait_for_server_status(self.id, 'ACTIVE')

        resp, server = self.client.get_server(self.id)
        self.assertEqual(self.flavor_ref_alt, server['flavor']['id'])

    @attr(type='smoke')
    @unittest.skipIf(not resize_available, 'Resize not available.')
    def test_resize_server_revert(self):
        """
        The server's RAM and disk space should return to its original
        values after a resize is reverted
        """

        self.client.resize(self.id, self.flavor_ref_alt)
        self.client.wait_for_server_status(id, 'VERIFY_RESIZE')

        self.client.revert_resize(self.id)
        self.client.wait_for_server_status(id, 'ACTIVE')

        resp, server = self.client.get_server(id)
        self.assertEqual(self.flavor_ref, server['flavor']['id'])
