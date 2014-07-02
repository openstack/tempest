# Copyright 2012 OpenStack Foundation
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
from tempest import test


class ServerMetadataTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setUpClass(cls):
        super(ServerMetadataTestJSON, cls).setUpClass()
        cls.client = cls.servers_client
        cls.quotas = cls.quotas_client
        resp, server = cls.create_test_server(meta={}, wait_until='ACTIVE')
        cls.server_id = server['id']

    def setUp(self):
        super(ServerMetadataTestJSON, self).setUp()
        meta = {'key1': 'value1', 'key2': 'value2'}
        resp, _ = self.client.set_server_metadata(self.server_id, meta)
        self.assertEqual(resp.status, 200)

    @test.attr(type='gate')
    def test_list_server_metadata(self):
        # All metadata key/value pairs for a server should be returned
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)

        # Verify the expected metadata items are in the list
        self.assertEqual(200, resp.status)
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @test.attr(type='gate')
    def test_set_server_metadata(self):
        # The server's metadata should be replaced with the provided values
        # Create a new set of metadata for the server
        req_metadata = {'meta2': 'data2', 'meta3': 'data3'}
        resp, metadata = self.client.set_server_metadata(self.server_id,
                                                         req_metadata)
        self.assertEqual(200, resp.status)

        # Verify the expected values are correct, and that the
        # previous values have been removed
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        self.assertEqual(resp_metadata, req_metadata)

    @test.attr(type='gate')
    def test_update_server_metadata(self):
        # The server's metadata values should be updated to the
        # provided values
        meta = {'key1': 'alt1', 'key3': 'value3'}
        resp, metadata = self.client.update_server_metadata(self.server_id,
                                                            meta)
        self.assertEqual(200, resp.status)

        # Verify the values have been updated to the proper values
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        expected = {'key1': 'alt1', 'key2': 'value2', 'key3': 'value3'}
        self.assertEqual(expected, resp_metadata)

    @test.attr(type='gate')
    def test_update_metadata_empty_body(self):
        # The original metadata should not be lost if empty metadata body is
        # passed
        meta = {}
        _, metadata = self.client.update_server_metadata(self.server_id, meta)
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @test.attr(type='gate')
    def test_get_server_metadata_item(self):
        # The value for a specific metadata key should be returned
        resp, meta = self.client.get_server_metadata_item(self.server_id,
                                                          'key2')
        self.assertEqual('value2', meta['key2'])

    @test.attr(type='gate')
    def test_set_server_metadata_item(self):
        # The item's value should be updated to the provided value
        # Update the metadata value
        meta = {'nova': 'alt'}
        resp, body = self.client.set_server_metadata_item(self.server_id,
                                                          'nova', meta)
        self.assertEqual(200, resp.status)

        # Verify the meta item's value has been updated
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        expected = {'key1': 'value1', 'key2': 'value2', 'nova': 'alt'}
        self.assertEqual(expected, resp_metadata)

    @test.attr(type='gate')
    def test_delete_server_metadata_item(self):
        # The metadata value/key pair should be deleted from the server
        resp, meta = self.client.delete_server_metadata_item(self.server_id,
                                                             'key1')
        self.assertEqual(204, resp.status)

        # Verify the metadata item has been removed
        resp, resp_metadata = self.client.list_server_metadata(self.server_id)
        expected = {'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)


class ServerMetadataTestXML(ServerMetadataTestJSON):
    _interface = 'xml'
