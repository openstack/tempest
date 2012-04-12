from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest import openstack
import tempest.config
from tempest.tests import utils
import unittest2 as unittest
from nose.plugins.attrib import attr


class TestServerDiskConfig(unittest.TestCase):

    resize_available = tempest.config.TempestConfig().compute.resize_available

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.servers_client
        extensions_client = cls.os.extensions_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.compute.image_ref
        cls.image_ref_alt = cls.config.compute.image_ref_alt
        cls.flavor_ref = cls.config.compute.flavor_ref
        cls.flavor_ref_alt = cls.config.compute.flavor_ref_alt
        cls.disk_config = extensions_client.is_enabled('DiskConfig')

    @attr(type='positive')
    @utils.skip_unless_attr('disk_config', 'Disk config extension not enabled')
    def test_create_server_with_manual_disk_config(self):
        """A server should be created with manual disk config"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='MANUAL')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    @utils.skip_unless_attr('disk_config', 'Disk config extension not enabled')
    def test_create_server_with_auto_disk_config(self):
        """A server should be created with auto disk config"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='AUTO')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    @utils.skip_unless_attr('disk_config', 'Disk config extension not enabled')
    def test_rebuild_server_with_manual_disk_config(self):
        """A server should be rebuilt using the manual disk config option"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='AUTO')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

        resp, server = self.client.rebuild(server['id'],
                                           self.image_ref_alt,
                                           disk_config='MANUAL')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    @utils.skip_unless_attr('disk_config', 'Disk config extension not enabled')
    def test_rebuild_server_with_auto_disk_config(self):
        """A server should be rebuilt using the auto disk config option"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='MANUAL')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

        resp, server = self.client.rebuild(server['id'],
                                           self.image_ref_alt,
                                           disk_config='AUTO')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Verify the specified attributes are set correctly
        resp, server = self.client.get_server(server['id'])
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    @utils.skip_unless_attr('disk_config', 'Disk config extension not enabled')
    @unittest.skipIf(not resize_available, 'Resize not available.')
    def test_resize_server_from_manual_to_auto(self):
        """A server should be resized from manual to auto disk config"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='MANUAL')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Resize with auto option
        self.client.resize(server['id'], self.flavor_ref_alt,
                           disk_config='AUTO')
        self.client.wait_for_server_status(server['id'], 'VERIFY_RESIZE')
        self.client.confirm_resize(server['id'])
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        resp, server = self.client.get_server(server['id'])
        self.assertEqual('AUTO', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])

    @attr(type='positive')
    @utils.skip_unless_attr('disk_config', 'Disk config extension not enabled')
    @unittest.skipIf(not resize_available, 'Resize not available.')
    def test_resize_server_from_auto_to_manual(self):
        """A server should be resized from auto to manual disk config"""
        name = rand_name('server')
        resp, server = self.client.create_server(name,
                                                 self.image_ref,
                                                 self.flavor_ref,
                                                 disk_config='AUTO')

        #Wait for the server to become active
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Resize with manual option
        self.client.resize(server['id'], self.flavor_ref_alt,
                           disk_config='MANUAL')
        self.client.wait_for_server_status(server['id'], 'VERIFY_RESIZE')
        self.client.confirm_resize(server['id'])
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        resp, server = self.client.get_server(server['id'])
        self.assertEqual('MANUAL', server['OS-DCF:diskConfig'])

        #Delete the server
        resp, body = self.client.delete_server(server['id'])
