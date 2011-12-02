from nose.plugins.attrib import attr
from storm import openstack
from storm.common.utils.data_utils import rand_name
import unittest2 as unittest
import storm.config

# Some module-level skip conditions
create_image_enabled = False


class ImagesTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.images_client
        cls.servers_client = cls.os.servers_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref
        create_image_enabled = cls.config.env.create_image_enabled

    def _parse_image_id(self, image_ref):
        temp = image_ref.rsplit('/')
        return temp[6]

    @unittest.skipIf(not create_image_enabled,
                    'Environment unable to create images.')
    def test_create_delete_image(self):
        """An image for the provided server should be created"""
        server_name = rand_name('server')
        resp, server = self.servers_client.create_server(server_name,
                                                         self.image_ref,
                                                         self.flavor_ref)
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        #Create a new image
        name = rand_name('image')
        resp, body = self.client.create_image(server['id'], name)
        image_id = self._parse_image_id(resp['location'])
        self.client.wait_for_image_resp_code(image_id, 200)
        self.client.wait_for_image_status(image_id, 'ACTIVE')

        #Verify the image was created correctly
        resp, image = self.client.get_image(image_id)
        self.assertEqual(name, image['name'])

        #Teardown
        self.client.delete_image(image['id'])
        self.servers_client.delete_server(server['id'])

    @attr(type='smoke')
    def test_get_image(self):
        """Returns the correct details for a single image"""
        resp, image = self.client.get_image(self.image_ref)
        self.assertEqual(self.image_ref, image['id'])

    @attr(type='smoke')
    def test_list_images(self):
        """The list of all images should contain the image flavor"""
        resp, images = self.client.list_images()
        found = any([i for i in images if i['id'] == self.image_ref])
        self.assertTrue(found)

    @attr(type='smoke')
    def test_list_images_with_detail(self):
        """Detailed list of all images should contain the expected image"""
        resp, images = self.client.list_images_with_detail()
        found = any([i for i in images if i['id'] == self.image_ref])
        self.assertTrue(found)
