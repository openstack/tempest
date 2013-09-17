# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.api.compute import base
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class ImagesMetadataTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ImagesMetadataTestJSON, cls).setUpClass()
        if not cls.config.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

        cls.servers_client = cls.servers_client
        cls.client = cls.images_client

        resp, server = cls.create_server(wait_until='ACTIVE')
        cls.server_id = server['id']

        # Snapshot the server once to save time
        name = rand_name('image')
        resp, _ = cls.client.create_image(cls.server_id, name, {})
        cls.image_id = resp['location'].rsplit('/', 1)[1]

        cls.client.wait_for_image_resp_code(cls.image_id, 200)
        cls.client.wait_for_image_status(cls.image_id, 'ACTIVE')

    @classmethod
    def tearDownClass(cls):
        cls.client.delete_image(cls.image_id)
        super(ImagesMetadataTestJSON, cls).tearDownClass()

    def setUp(self):
        super(ImagesMetadataTestJSON, self).setUp()
        meta = {'key1': 'value1', 'key2': 'value2'}
        resp, _ = self.client.set_image_metadata(self.image_id, meta)
        self.assertEqual(resp.status, 200)

    @attr(type='gate')
    def test_list_image_metadata(self):
        # All metadata key/value pairs for an image should be returned
        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @attr(type='gate')
    def test_set_image_metadata(self):
        # The metadata for the image should match the new values
        req_metadata = {'meta2': 'value2', 'meta3': 'value3'}
        resp, body = self.client.set_image_metadata(self.image_id,
                                                    req_metadata)

        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        self.assertEqual(req_metadata, resp_metadata)

    @attr(type='gate')
    def test_update_image_metadata(self):
        # The metadata for the image should match the updated values
        req_metadata = {'key1': 'alt1', 'key3': 'value3'}
        resp, metadata = self.client.update_image_metadata(self.image_id,
                                                           req_metadata)

        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'key1': 'alt1', 'key2': 'value2', 'key3': 'value3'}
        self.assertEqual(expected, resp_metadata)

    @attr(type='gate')
    def test_get_image_metadata_item(self):
        # The value for a specific metadata key should be returned
        resp, meta = self.client.get_image_metadata_item(self.image_id,
                                                         'key2')
        self.assertEqual('value2', meta['key2'])

    @attr(type='gate')
    def test_set_image_metadata_item(self):
        # The value provided for the given meta item should be set for
        # the image
        meta = {'key1': 'alt'}
        resp, body = self.client.set_image_metadata_item(self.image_id,
                                                         'key1', meta)
        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'key1': 'alt', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @attr(type='gate')
    def test_delete_image_metadata_item(self):
        # The metadata value/key pair should be deleted from the image
        resp, body = self.client.delete_image_metadata_item(self.image_id,
                                                            'key1')
        resp, resp_metadata = self.client.list_image_metadata(self.image_id)
        expected = {'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @attr(type=['negative', 'gate'])
    def test_list_nonexistant_image_metadata(self):
        # Negative test: List on nonexistant image
        # metadata should not happen
        self.assertRaises(exceptions.NotFound, self.client.list_image_metadata,
                          999)

    @attr(type=['negative', 'gate'])
    def test_update_nonexistant_image_metadata(self):
        # Negative test:An update should not happen for a non-existent image
        meta = {'key1': 'alt1', 'key2': 'alt2'}
        self.assertRaises(exceptions.NotFound,
                          self.client.update_image_metadata, 999, meta)

    @attr(type=['negative', 'gate'])
    def test_get_nonexistant_image_metadata_item(self):
        # Negative test: Get on non-existent image should not happen
        self.assertRaises(exceptions.NotFound,
                          self.client.get_image_metadata_item, 999, 'key2')

    @attr(type=['negative', 'gate'])
    def test_set_nonexistant_image_metadata(self):
        # Negative test: Metadata should not be set to a non-existent image
        meta = {'key1': 'alt1', 'key2': 'alt2'}
        self.assertRaises(exceptions.NotFound, self.client.set_image_metadata,
                          999, meta)

    @attr(type=['negative', 'gate'])
    def test_set_nonexistant_image_metadata_item(self):
        # Negative test: Metadata item should not be set to a
        # nonexistant image
        meta = {'key1': 'alt'}
        self.assertRaises(exceptions.NotFound,
                          self.client.set_image_metadata_item, 999, 'key1',
                          meta)

    @attr(type=['negative', 'gate'])
    def test_delete_nonexistant_image_metadata_item(self):
        # Negative test: Shouldn't be able to delete metadata
        # item from non-existent image
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_image_metadata_item, 999, 'key1')


class ImagesMetadataTestXML(ImagesMetadataTestJSON):
    _interface = 'xml'
