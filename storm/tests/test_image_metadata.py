from nose.plugins.attrib import attr
from storm import openstack
from storm.common.utils.data_utils import rand_name
import storm.config
import unittest2 as unittest


class ImagesMetadataTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.servers_client = cls.os.servers_client
        cls.client = cls.os.images_client
        cls.config = cls.os.config
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref
        cls.ssh_timeout = cls.config.nova.ssh_timeout

        name = rand_name('server')
        resp, cls.server = cls.servers_client.create_server(name,
                                                            cls.image_ref,
                                                            cls.flavor_ref)
        #Wait for the server to become active
        cls.servers_client.wait_for_server_status(cls.server['id'], 'ACTIVE')

        #Create an image from the server
        name = rand_name('image')
        cls.meta = {'key1': 'value1', 'key2': 'value2'}
        resp, body = cls.client.create_image(cls.server['id'], name, cls.meta)
        image_ref = resp['location']
        temp = image_ref.rsplit('/')
        image_id = temp[len(temp) - 1]

        cls.client.wait_for_image_resp_code(image_id, 200)
        cls.client.wait_for_image_status(image_id, 'ACTIVE')
        resp, cls.image = cls.client.get_image(image_id)

    @classmethod
    def tearDownClass(cls):
        cls.servers_client.delete_server(cls.server['id'])
        cls.client.delete_image(cls.image['id'])

    def _parse_image_id(self, image_ref):
        temp = image_ref.rsplit('/')
        return len(temp) - 1

    def test_list_image_metadata(self):
        """All metadata key/value pairs for an image should be returned"""
        resp, metadata = self.client.list_image_metadata(self.image['id'])
        self.assertEqual('value1', metadata['key1'])
        self.assertEqual('value2', metadata['key2'])

    def test_set_image_metadata(self):
        """The metadata for the image should match the new values"""
        meta = {'meta1': 'data1'}
        name = rand_name('server')
        resp, server = self.servers_client.create_server(name, self.image_ref,
                                                self.flavor_ref)
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        name = rand_name('image')
        resp, body = self.client.create_image(server['id'], name, meta)
        image_id = self._parse_image_id(resp['location'])
        self.client.wait_for_image_resp_code(image_id, 200)
        self.client.wait_for_image_status(image_id, 'ACTIVE')
        resp, image = self.client.get_image(image_id)

        meta = {'meta2': 'data2', 'meta3': 'data3'}
        resp, body = self.client.set_image_metadata(image['id'], meta)

        resp, metadata = self.client.list_image_metadata(image['id'])
        self.assertEqual('data2', metadata['meta2'])
        self.assertEqual('data3', metadata['meta3'])
        self.assertTrue('meta1' not in metadata)

        self.servers_client.delete_server(server['id'])
        self.client.delete_image(image['id'])

    def test_update_image_metadata(self):
        """The metadata for the image should match the updated values"""
        meta = {'key1': 'value1', 'key2': 'value2'}
        name = rand_name('server')
        resp, server = self.servers_client.create_server(name, self.image_ref,
                                                self.flavor_ref)
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        name = rand_name('image')
        resp, body = self.client.create_image(server['id'], name, meta)
        image_id = self._parse_image_id(resp['location'])
        self.client.wait_for_image_resp_code(image_id, 200)
        self.client.wait_for_image_status(image_id, 'ACTIVE')
        resp, image = self.client.get_image(image_id)

        meta = {'key1': 'alt1', 'key2': 'alt2'}
        resp, metadata = self.client.update_image_metadata(image['id'], meta)

        resp, metadata = self.client.list_image_metadata(image['id'])
        self.assertEqual('alt1', metadata['key1'])
        self.assertEqual('alt2', metadata['key2'])

        self.servers_client.delete_server(server['id'])
        self.client.delete_image(image['id'])

    def test_get_image_metadata_item(self):
        """The value for a specic metadata key should be returned"""
        resp, meta = self.client.get_image_metadata_item(self.image['id'],
                                                         'key2')
        self.assertTrue('value2', meta['key2'])

    def test_set_image_metadata_item(self):
        """
        The value provided for the given meta item should be set for the image
        """
        meta = {'nova': 'server'}
        name = rand_name('server')
        resp, server = self.servers_client.create_server(name, self.image_ref,
                                                self.flavor_ref)
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        name = rand_name('image')
        resp, body = self.client.create_image(server['id'], name, meta)
        image_id = self._parse_image_id(resp['location'])
        self.client.wait_for_image_resp_code(image_id, 200)
        self.client.wait_for_image_status(image_id, 'ACTIVE')
        resp, image = self.client.get_image(image_id)

        meta = {'nova': 'alt'}
        resp, body = self.client.set_image_metadata_item(image['id'],
                                                         'nova', meta)
        resp, metadata = self.client.list_image_metadata(image['id'])
        self.assertEqual('alt', metadata['nova'])

        self.servers_client.delete_server(server['id'])
        self.client.delete_image(image['id'])

    def test_delete_image_metadata_item(self):
        """The metadata value/key pair should be deleted from the image"""
        meta = {'delkey': 'delvalue'}
        name = rand_name('server')
        resp, server = self.servers_client.create_server(name, self.image_ref,
                                                self.flavor_ref)
        self.servers_client.wait_for_server_status(server['id'], 'ACTIVE')

        name = rand_name('image')
        resp, body = self.client.create_image(server['id'], name, meta)
        image_id = self._parse_image_id(resp['location'])
        self.client.wait_for_image_resp_code(image_id, 200)
        self.client.wait_for_image_status(image_id, 'ACTIVE')
        resp, image = self.client.get_image(image_id)

        resp, body = self.client.delete_image_metadata_item(image['id'],
                                                            'delkey')
        resp, metadata = self.client.list_image_metadata(image['id'])
        self.assertTrue('delkey' not in metadata)

        self.servers_client.delete_server(server['id'])
        self.client.delete_image(image['id'])
