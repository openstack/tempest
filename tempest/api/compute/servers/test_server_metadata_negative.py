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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class ServerMetadataNegativeTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(ServerMetadataNegativeTestJSON, cls).setup_clients()
        cls.client = cls.servers_client
        cls.quotas = cls.quotas_client

    @classmethod
    def resource_setup(cls):
        super(ServerMetadataNegativeTestJSON, cls).resource_setup()
        cls.tenant_id = cls.client.tenant_id
        server = cls.create_test_server(meta={}, wait_until='ACTIVE')

        cls.server_id = server['id']

    @test.attr(type=['gate', 'negative'])
    @test.idempotent_id('fe114a8f-3a57-4eff-9ee2-4e14628df049')
    def test_server_create_metadata_key_too_long(self):
        # Attempt to start a server with a meta-data key that is > 255
        # characters

        # Tryset_server_metadata_item a few values
        for sz in [256, 257, 511, 1023]:
            key = "k" * sz
            meta = {key: 'data1'}
            self.assertRaises((lib_exc.BadRequest, lib_exc.OverLimit),
                              self.create_test_server,
                              meta=meta)

        # no teardown - all creates should fail

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('92431555-4d8b-467c-b95b-b17daa5e57ff')
    def test_create_server_metadata_blank_key(self):
        # Blank key should trigger an error.
        meta = {'': 'data1'}
        self.assertRaises(lib_exc.BadRequest,
                          self.create_test_server,
                          meta=meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('4d9cd7a3-2010-4b41-b8fe-3bbf0b169466')
    def test_server_metadata_non_existent_server(self):
        # GET on a non-existent server should not succeed
        non_existent_server_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.client.get_server_metadata_item,
                          non_existent_server_id,
                          'test2')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f408e78e-3066-4097-9299-3b0182da812e')
    def test_list_server_metadata_non_existent_server(self):
        # List metadata on a non-existent server should not succeed
        non_existent_server_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.client.list_server_metadata,
                          non_existent_server_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0025fbd6-a4ba-4cde-b8c2-96805dcfdabc')
    def test_wrong_key_passed_in_body(self):
        # Raise BadRequest if key in uri does not match
        # the key passed in body.
        meta = {'testkey': 'testvalue'}
        self.assertRaises(lib_exc.BadRequest,
                          self.client.set_server_metadata_item,
                          self.server_id, 'key', meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0df38c2a-3d4e-4db5-98d8-d4d9fa843a12')
    def test_set_metadata_non_existent_server(self):
        # Set metadata on a non-existent server should not succeed
        non_existent_server_id = data_utils.rand_uuid()
        meta = {'meta1': 'data1'}
        self.assertRaises(lib_exc.NotFound,
                          self.client.set_server_metadata,
                          non_existent_server_id,
                          meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('904b13dc-0ef2-4e4c-91cd-3b4a0f2f49d8')
    def test_update_metadata_non_existent_server(self):
        # An update should not happen for a non-existent server
        non_existent_server_id = data_utils.rand_uuid()
        meta = {'key1': 'value1', 'key2': 'value2'}
        self.assertRaises(lib_exc.NotFound,
                          self.client.update_server_metadata,
                          non_existent_server_id,
                          meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('a452f38c-05c2-4b47-bd44-a4f0bf5a5e48')
    def test_update_metadata_with_blank_key(self):
        # Blank key should trigger an error
        meta = {'': 'data1'}
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_server_metadata,
                          self.server_id, meta=meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('6bbd88e1-f8b3-424d-ba10-ae21c45ada8d')
    def test_delete_metadata_non_existent_server(self):
        # Should not be able to delete metadata item from a non-existent server
        non_existent_server_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.client.delete_server_metadata_item,
                          non_existent_server_id,
                          'd')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('d8c0a210-a5c3-4664-be04-69d96746b547')
    def test_metadata_items_limit(self):
        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised while exceeding metadata items limit for
        # tenant.
        quota_set = self.quotas.get_quota_set(self.tenant_id)
        quota_metadata = quota_set['metadata_items']
        if quota_metadata == -1:
            raise self.skipException("No limit for metadata_items")

        req_metadata = {}
        for num in range(1, quota_metadata + 2):
            req_metadata['key' + str(num)] = 'val' + str(num)
        self.assertRaises((lib_exc.OverLimit, lib_exc.Forbidden),
                          self.client.set_server_metadata,
                          self.server_id, req_metadata)

        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised while exceeding metadata items limit for
        # tenant.
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.client.update_server_metadata,
                          self.server_id, req_metadata)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('96100343-7fa9-40d8-80fa-d29ef588ce1c')
    def test_set_server_metadata_blank_key(self):
        # Raise a bad request error for blank key.
        # set_server_metadata will replace all metadata with new value
        meta = {'': 'data1'}
        self.assertRaises(lib_exc.BadRequest,
                          self.client.set_server_metadata,
                          self.server_id, meta=meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('64a91aee-9723-4863-be44-4c9d9f1e7d0e')
    def test_set_server_metadata_missing_metadata(self):
        # Raise a bad request error for a missing metadata field
        # set_server_metadata will replace all metadata with new value
        meta = {'meta1': 'data1'}
        self.assertRaises(lib_exc.BadRequest,
                          self.client.set_server_metadata,
                          self.server_id, meta=meta, no_metadata_field=True)
