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
from tempest.lib import decorators


class ServerMetadataTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(ServerMetadataTestJSON, cls).setup_clients()
        cls.client = cls.servers_client

    @classmethod
    def resource_setup(cls):
        super(ServerMetadataTestJSON, cls).resource_setup()
        cls.server = cls.create_test_server(metadata={}, wait_until='ACTIVE')

    def setUp(self):
        super(ServerMetadataTestJSON, self).setUp()
        meta = {'key1': 'value1', 'key2': 'value2'}
        self.client.set_server_metadata(self.server['id'], meta)

    @decorators.idempotent_id('479da087-92b3-4dcf-aeb3-fd293b2d14ce')
    def test_list_server_metadata(self):
        # All metadata key/value pairs for a server should be returned
        resp_metadata = (self.client.list_server_metadata(self.server['id'])
                         ['metadata'])

        # Verify the expected metadata items are in the list
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @decorators.idempotent_id('211021f6-21de-4657-a68f-908878cfe251')
    def test_set_server_metadata(self):
        # The server's metadata should be replaced with the provided values
        # Create a new set of metadata for the server
        req_metadata = {'meta2': 'data2', 'meta3': 'data3'}
        self.client.set_server_metadata(self.server['id'], req_metadata)

        # Verify the expected values are correct, and that the
        # previous values have been removed
        resp_metadata = (self.client.list_server_metadata(self.server['id'])
                         ['metadata'])
        self.assertEqual(resp_metadata, req_metadata)

    @decorators.idempotent_id('344d981e-0c33-4997-8a5d-6c1d803e4134')
    def test_update_server_metadata(self):
        # The server's metadata values should be updated to the
        # provided values
        meta = {'key1': 'alt1', 'key3': 'value3'}
        self.client.update_server_metadata(self.server['id'], meta)

        # Verify the values have been updated to the proper values
        resp_metadata = (self.client.list_server_metadata(self.server['id'])
                         ['metadata'])
        expected = {'key1': 'alt1', 'key2': 'value2', 'key3': 'value3'}
        self.assertEqual(expected, resp_metadata)

    @decorators.idempotent_id('0f58d402-e34a-481d-8af8-b392b17426d9')
    def test_update_metadata_empty_body(self):
        # The original metadata should not be lost if empty metadata body is
        # passed
        meta = {}
        self.client.update_server_metadata(self.server['id'], meta)
        resp_metadata = (self.client.list_server_metadata(self.server['id'])
                         ['metadata'])
        expected = {'key1': 'value1', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)

    @decorators.idempotent_id('3043c57d-7e0e-49a6-9a96-ad569c265e6a')
    def test_get_server_metadata_item(self):
        # The value for a specific metadata key should be returned
        meta = self.client.show_server_metadata_item(self.server['id'],
                                                     'key2')['meta']
        self.assertEqual('value2', meta['key2'])

    @decorators.idempotent_id('58c02d4f-5c67-40be-8744-d3fa5982eb1c')
    def test_set_server_metadata_item(self):
        # The item's value should be updated to the provided value
        # Update the metadata value
        meta = {'nova': 'alt'}
        self.client.set_server_metadata_item(self.server['id'], 'nova', meta)

        # Verify the meta item's value has been updated
        resp_metadata = (self.client.list_server_metadata(self.server['id'])
                         ['metadata'])
        expected = {'key1': 'value1', 'key2': 'value2', 'nova': 'alt'}
        self.assertEqual(expected, resp_metadata)

    @decorators.idempotent_id('127642d6-4c7b-4486-b7cd-07265a378658')
    def test_delete_server_metadata_item(self):
        # The metadata value/key pair should be deleted from the server
        self.client.delete_server_metadata_item(self.server['id'], 'key1')

        # Verify the metadata item has been removed
        resp_metadata = (self.client.list_server_metadata(self.server['id'])
                         ['metadata'])
        expected = {'key2': 'value2'}
        self.assertEqual(expected, resp_metadata)
