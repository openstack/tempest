
import json

from kong import openstack
from kong import tests


class ServersMetadataTest(tests.FunctionalTest):
    @classmethod
    def setUpClass(self):
        super(ServersMetadataTest, self).setUp()
        self.os = openstack.Manager(self.nova)
        self.image_ref = self.os.config.env.image_ref
        self.flavor_ref = self.os.config.env.flavor_ref

    def setUp(self):
        server = {
            'name' : 'testserver',
            'imageRef' : self.image_ref,
            'flavorRef' : self.flavor_ref,
            'metadata' : {
                'testEntry' : 'testValue',
            },
        }

        created_server = self.os.nova.create_server(server)
        self.server_id = created_server['id']

    def tearDown(self):
        self.os.nova.delete_server(self.server_id)


    def test_get_server_metadata(self):
        """Retrieve metadata for a server"""

        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)

        result = json.loads(body)
        expected = {
            'metadata' : {
                'testEntry' : 'testValue',
            },
        }
        self.assertEqual(expected, result)

    def test_post_server_metadata(self):
        """Create or update metadata for a server"""

        post_metadata = {
            'metadata' : {
                'new_entry1' : 'new_value1',
                'new_entry2' : 'new_value2',
            },
        }
        post_body = json.dumps(post_metadata)

        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('POST', url, body=post_body)
        self.assertEqual(200, response.status)

        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)

        result = json.loads(body)
        expected = post_metadata
        expected['metadata']['testEntry'] = 'testValue'
        self.assertEqual(expected, result)

    def test_put_server_metadata(self):
        """Overwrite all metadata for a server"""

        expected = {
            'metadata' : {
                'new_entry1' : 'new_value1',
                'new_entry2' : 'new_value2',
            },
        }

        url = '/servers/%s/metadata' % self.server_id
        post_body = json.dumps(expected)
        response, body = self.os.nova.request('PUT', url, body=post_body)
        self.assertEqual(200, response.status)

        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)

        result = json.loads(body)
        # We want to make sure 'testEntry' was removed
        self.assertEqual(expected, result)

    def test_get_server_metadata_key(self):
        """Retrieve specific metadata key for a server"""

        url = '/servers/%s/metadata/testEntry' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEqual(200, response.status)

        result = json.loads(body)
        expected = {
            'meta':{
                'testEntry':'testValue',
            },
        }

        self.assertDictEqual(expected, result)

    def test_add_server_metadata_key(self):
        """Set specific metadata key on a server"""

        expected_meta = {
            'meta' : {
                'new_meta1' : 'new_value1',
            },
        }

        put_body = json.dumps(expected_meta)

        url = '/servers/%s/metadata/new_meta1' % self.server_id
        response, body = self.os.nova.request('PUT', url, body=put_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertDictEqual(expected_meta, result)

        expected_metadata = {
            'metadata' : {
                'testEntry' : 'testValue',
                'new_meta1' : 'new_value1',
            },
        }

        # Now check all metadata to make sure the other values are there
        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        result = json.loads(body)
        self.assertDictEqual(expected_metadata, result)

    def test_update_server_metadata_key(self):
        """Update specific metadata key for a server"""

        expected_meta = {
            'meta' : {
                'testEntry' : 'testValue2',
            },
        }
        put_body = json.dumps(expected_meta)

        url = '/servers/%s/metadata/testEntry' % self.server_id
        response, body = self.os.nova.request('PUT', url, body=put_body)
        self.assertEqual(200, response.status)
        result = json.loads(body)
        self.assertEqual(expected_meta, result)

    def test_delete_server_metadata_key(self):
        """Delete metadata for a server"""

        url = '/servers/%s/metadata/testEntry' % self.server_id
        response, body = self.os.nova.request('DELETE', url)
        self.assertEquals(204, response.status)

        url = '/servers/%s/metadata/testEntry' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEquals(404, response.status)

        url = '/servers/%s/metadata' % self.server_id
        response, body = self.os.nova.request('GET', url)
        self.assertEquals(200, response.status)
        result = json.loads(body)
        self.assertDictEqual({'metadata':{}}, result)
