import unittest2 as unittest

import nose.plugins.skip

from tempest import openstack
from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
from tempest.tests import utils


class ServerDetailsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.servers_client
        cls.images_client = cls.os.images_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref
        cls.image_ref_alt = cls.config.env.image_ref_alt
        cls.flavor_ref_alt = cls.config.env.flavor_ref_alt

        # Check to see if the alternate image ref actually exists...
        images_client = cls.os.images_client
        resp, images = images_client.list_images()

        if cls.image_ref != cls.image_ref_alt and \
            any([image for image in images
                 if image['id'] == cls.image_ref_alt]):
            cls.multiple_images = True
        else:
            cls.image_ref_alt = cls.image_ref

        # Do some sanity checks here. If one of the images does
        # not exist, fail early since the tests won't work...
        try:
            cls.images_client.get_image(cls.image_ref)
        except exceptions.NotFound:
            raise RuntimeError("Image %s (image_ref) was not found!" %
                               cls.image_ref)

        try:
            cls.images_client.get_image(cls.image_ref_alt)
        except exceptions.NotFound:
            raise RuntimeError("Image %s (image_ref_alt) was not found!" %
                               cls.image_ref_alt)

        cls.s1_name = rand_name('server')
        resp, server = cls.client.create_server(cls.s1_name, cls.image_ref,
                                                cls.flavor_ref)
        cls.client.wait_for_server_status(server['id'], 'ACTIVE')
        resp, cls.s1 = cls.client.get_server(server['id'])

        cls.s2_name = rand_name('server')
        resp, server = cls.client.create_server(cls.s2_name, cls.image_ref_alt,
                                                cls.flavor_ref)
        cls.client.wait_for_server_status(server['id'], 'ACTIVE')
        resp, cls.s2 = cls.client.get_server(server['id'])

        cls.s3_name = rand_name('server')
        resp, server = cls.client.create_server(cls.s3_name, cls.image_ref,
                                                cls.flavor_ref_alt)
        cls.client.wait_for_server_status(server['id'], 'ACTIVE')
        resp, cls.s3 = cls.client.get_server(server['id'])

    @classmethod
    def tearDownClass(cls):
        cls.client.delete_server(cls.s1['id'])
        cls.client.delete_server(cls.s2['id'])
        cls.client.delete_server(cls.s3['id'])

    def test_list_servers_with_detail(self):
        """ Return a detailed list of all servers """
        resp, body = self.client.list_servers_with_detail()
        servers = body['servers']

        self.assertTrue(self.s1 in servers)
        self.assertTrue(self.s2 in servers)
        self.assertTrue(self.s3 in servers)

    @utils.skip_unless_attr('multiple_images', 'Only one image found')
    def test_list_servers_detailed_filter_by_image(self):
        """Filter the detailed list of servers by image"""
        params = {'image': self.image_ref}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertTrue(self.s1 in servers)
        self.assertTrue(self.s2 not in servers)
        self.assertTrue(self.s3 in servers)

    def test_list_servers_detailed_filter_by_flavor(self):
        """Filter the detailed list of servers by flavor"""
        params = {'flavor': self.flavor_ref_alt}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertTrue(self.s1 not in servers)
        self.assertTrue(self.s2 not in servers)
        self.assertTrue(self.s3 in servers)

    def test_list_servers_detailed_filter_by_server_name(self):
        """Filter the detailed list of servers by server name"""
        params = {'name': self.s1_name}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertTrue(self.s1 in servers)
        self.assertTrue(self.s2 not in servers)
        self.assertTrue(self.s3 not in servers)

    def test_list_servers_detailed_filter_by_server_status(self):
        """Filter the detailed list of servers by server status"""
        params = {'status': 'active'}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertTrue(self.s1 in servers)
        self.assertTrue(self.s2 in servers)
        self.assertTrue(self.s3 in servers)

    def test_get_server_details(self):
        """Return the full details of a single server"""
        resp, server = self.client.get_server(self.s1['id'])

        self.assertEqual(self.s1_name, server['name'])
        self.assertEqual(self.image_ref, server['image']['id'])
        self.assertEqual(str(self.flavor_ref), server['flavor']['id'])
