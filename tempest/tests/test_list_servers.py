import unittest2 as unittest

import nose.plugins.skip

from tempest import openstack
from tempest import exceptions
from base_compute_test import BaseComputeTest
from tempest.common.utils.data_utils import rand_name
from tempest.tests import utils


class ServerDetailsTest(BaseComputeTest):

    @classmethod
    def setUpClass(cls):
        cls.client = cls.servers_client

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
        resp, cls.s1 = cls.client.create_server(cls.s1_name, cls.image_ref,
                                                cls.flavor_ref)
        cls.s2_name = rand_name('server')
        resp, cls.s2 = cls.client.create_server(cls.s2_name, cls.image_ref_alt,
                                                cls.flavor_ref)
        cls.s3_name = rand_name('server')
        resp, cls.s3 = cls.client.create_server(cls.s3_name, cls.image_ref,
                                                cls.flavor_ref_alt)

        cls.client.wait_for_server_status(cls.s1['id'], 'ACTIVE')
        resp, cls.s1 = cls.client.get_server(cls.s1['id'])
        cls.client.wait_for_server_status(cls.s2['id'], 'ACTIVE')
        resp, cls.s2 = cls.client.get_server(cls.s2['id'])
        cls.client.wait_for_server_status(cls.s3['id'], 'ACTIVE')
        resp, cls.s3 = cls.client.get_server(cls.s3['id'])

        # The list server call returns minimal results, so we need
        # a less detailed version of each server also
        cls.s1_min = cls._convert_to_min_details(cls.s1)
        cls.s2_min = cls._convert_to_min_details(cls.s2)
        cls.s3_min = cls._convert_to_min_details(cls.s3)

    @classmethod
    def tearDownClass(cls):
        cls.client.delete_server(cls.s1['id'])
        cls.client.delete_server(cls.s2['id'])
        cls.client.delete_server(cls.s3['id'])

    def test_list_servers(self):
        """Return a list of all servers"""
        resp, body = self.client.list_servers()
        servers = body['servers']

        self.assertTrue(self.s1_min in servers)
        self.assertTrue(self.s2_min in servers)
        self.assertTrue(self.s3_min in servers)

    @utils.skip_unless_attr('multiple_images', 'Only one image found')
    def test_list_servers_filter_by_image(self):
        """Filter the list of servers by image"""
        params = {'image': self.image_ref}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertTrue(self.s1_min in servers)
        self.assertTrue(self.s2_min not in servers)
        self.assertTrue(self.s3_min in servers)

    def test_list_servers_filter_by_flavor(self):
        """Filter the list of servers by flavor"""
        params = {'flavor': self.flavor_ref_alt}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertTrue(self.s1_min not in servers)
        self.assertTrue(self.s2_min not in servers)
        self.assertTrue(self.s3_min in servers)

    def test_list_servers_filter_by_server_name(self):
        """Filter the list of servers by server name"""
        params = {'name': self.s1_name}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertTrue(self.s1_min in servers)
        self.assertTrue(self.s2_min not in servers)
        self.assertTrue(self.s3_min not in servers)

    def test_list_servers_filter_by_server_status(self):
        """Filter the list of servers by server status"""
        params = {'status': 'active'}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertTrue(self.s1_min in servers)
        self.assertTrue(self.s2_min in servers)
        self.assertTrue(self.s3_min in servers)

    def test_list_servers_limit_results(self):
        """Verify only the expected number of servers are returned"""
        params = {'limit': 1}
        resp, servers = self.client.list_servers_with_detail(params)
        self.assertEqual(1, len(servers['servers']))

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

    def test_list_servers_detailed_limit_results(self):
        """Verify only the expected number of detailed results are returned"""
        params = {'limit': 1}
        resp, servers = self.client.list_servers_with_detail(params)
        self.assertEqual(1, len(servers['servers']))

    def test_get_server_details(self):
        """Return the full details of a single server"""
        resp, server = self.client.get_server(self.s1['id'])

        self.assertEqual(self.s1_name, server['name'])
        self.assertEqual(self.image_ref, server['image']['id'])
        self.assertEqual(str(self.flavor_ref), server['flavor']['id'])

    @classmethod
    def _convert_to_min_details(self, server):
        min_detail = {}
        min_detail['name'] = server['name']
        min_detail['links'] = server['links']
        min_detail['id'] = server['id']
        return min_detail
