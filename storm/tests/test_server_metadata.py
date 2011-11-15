from nose.plugins.attrib import attr
from storm import openstack
from storm.common.utils.data_utils import rand_name
import unittest2 as unittest
import storm.config


class ServerMetadataTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.os = openstack.Manager()
        cls.client = cls.os.servers_client
        cls.config = storm.config.StormConfig()
        cls.image_ref = cls.config.env.image_ref
        cls.flavor_ref = cls.config.env.flavor_ref

        #Create a server to be used for all read only tests
        cls.meta = {'test1': 'value1', 'test2': 'value2'}
        name = rand_name('server')
        resp, cls.server = cls.client.create_server(name, cls.image_ref,
                                                cls.flavor_ref, meta=cls.meta)

        #Wait for the server to become active
        cls.client.wait_for_server_status(cls.server['id'], 'ACTIVE')

    @classmethod
    def tearDownClass(cls):
        cls.client.delete_server(cls.server['id'])

    def test_list_server_metadata(self):
        """All metadata key/value pairs for a server should be returned"""
        resp, metadata = self.client.list_server_metadata(self.server['id'])

        #Verify the expected metadata items are in the list
        self.assertEqual(200, resp.status)
        self.assertEqual('value1', metadata['test1'])
        self.assertEqual('value2', metadata['test2'])

    def test_set_server_metadata(self):
        """The server's metadata should be replaced with the provided values"""
        meta = {'meta1': 'data1'}
        name = rand_name('server')
        resp, server = self.client.create_server(name, self.image_ref,
                                                self.flavor_ref, meta=meta)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Create a new set of metadata for the server
        meta = {'meta2': 'data2', 'meta3': 'data3'}
        resp, metadata = self.client.set_server_metadata(server['id'], meta)
        self.assertEqual(200, resp.status)

        #Verify the expected values are correct, and that the
        #previous values have been removed
        resp, body = self.client.list_server_metadata(server['id'])
        self.assertEqual('data2', metadata['meta2'])
        self.assertEqual('data3', metadata['meta3'])
        self.assertTrue('meta1' not in metadata)

        #Teardown
        self.client.delete_server(server['id'])

    def test_update_server_metadata(self):
        """
        The server's metadata values should be updated to the
        provided values
        """
        meta = {'key1': 'value1', 'key2': 'value2'}
        name = rand_name('server')
        resp, server = self.client.create_server(name, self.image_ref,
                                                self.flavor_ref, meta=meta)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Update all metadata items for the server
        meta = {'key1': 'alt1', 'key2': 'alt2'}
        resp, metadata = self.client.update_server_metadata(server['id'], meta)
        self.assertEqual(200, resp.status)

        #Verify the values have been updated to the proper values
        resp, body = self.client.list_server_metadata(server['id'])
        self.assertEqual('alt1', metadata['key1'])
        self.assertEqual('alt2', metadata['key2'])

        #Teardown
        self.client.delete_server(server['id'])

    def test_get_server_metadata_item(self):
        """ The value for a specic metadata key should be returned """
        resp, meta = self.client.get_server_metadata_item(self.server['id'],
                                                          'test2')
        self.assertTrue('value2', meta['test2'])

    def test_set_server_metadata_item(self):
        """The item's value should be updated to the provided value"""
        meta = {'nova': 'server'}
        name = rand_name('server')
        resp, server = self.client.create_server(name, self.image_ref,
                                                self.flavor_ref, meta=meta)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Update the metadata value
        meta = {'nova': 'alt'}
        resp, body = self.client.set_server_metadata_item(server['id'],
                                                          'nova', meta)
        self.assertEqual(200, resp.status)

        #Verify the meta item's value has been updated
        resp, body = self.client.list_server_metadata(server['id'])
        self.assertEqual('alt', metadata['nova'])

        #Teardown
        self.client.delete_server(server.id)

    def test_delete_server_metadata_item(self):
        """The metadata value/key pair should be deleted from the server"""
        meta = {'delkey': 'delvalue'}
        name = rand_name('server')
        resp, server = self.client.create_server(name, self.image_ref,
                                                self.flavor_ref, meta=meta)
        self.client.wait_for_server_status(server['id'], 'ACTIVE')

        #Delete the metadata item
        resp, metadata = self.client.delete_server_metadata_item(server['id'],
                                                                 'delkey')
        self.assertEqual(204, resp.status)

        #Verify the metadata item has been removed
        resp, metadata = self.client.list_server_metadata(server['id'])
        self.assertTrue('delkey' not in metadata)

        #Teardown
        self.client.delete_server(server['id'])
