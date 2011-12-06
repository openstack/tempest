from nose.plugins.attrib import attr
from tempest import openstack
from tempest.common.utils.data_utils import rand_name
import unittest2 as unittest
import tempest.config


class ListImagesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.images_client
        cls.servers_client = cls.os.servers_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref

    @attr(type='smoke')
    def test_get_image(self):
        """Returns the correct details for a single image"""
        resp, image = self.client.get_image(self.image_ref)
        self.assertEqual(self.image_ref, image['id'])

    @attr(type='smoke')
    def test_list_images(self):
        """The list of all images should contain the image"""
        resp, images = self.client.list_images()
        found = any([i for i in images if i['id'] == self.image_ref])
        self.assertTrue(found)

    @attr(type='smoke')
    def test_list_images_with_detail(self):
        """Detailed list of all images should contain the expected image"""
        resp, images = self.client.list_images_with_detail()
        found = any([i for i in images if i['id'] == self.image_ref])
        self.assertTrue(found)
