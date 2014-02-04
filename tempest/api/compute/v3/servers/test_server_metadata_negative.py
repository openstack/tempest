# Copyright 2014 NEC Corporation.  All rights reserved.
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
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class ServerMetadataV3NegativeTest(base.BaseV3ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ServerMetadataV3NegativeTest, cls).setUpClass()
        cls.client = cls.servers_client
        cls.quotas = cls.quotas_client
        cls.admin_client = cls._get_identity_admin_client()
        resp, tenants = cls.admin_client.list_tenants()
        cls.tenant_id = [tnt['id'] for tnt in tenants if tnt['name'] ==
                         cls.client.tenant_name][0]
        resp, server = cls.create_test_server(meta={}, wait_until='ACTIVE')

        cls.server_id = server['id']

    @test.attr(type=['gate', 'negative'])
    def test_server_create_metadata_key_too_long(self):
        # Attempt to start a server with a meta-data key that is > 255
        # characters

        # Tryset_server_metadata_item a few values
        for sz in [256, 257, 511, 1023]:
            key = "k" * sz
            meta = {key: 'data1'}
            self.assertRaises(exceptions.OverLimit,
                              self.create_test_server,
                              meta=meta)

        # no teardown - all creates should fail

    @test.attr(type=['negative', 'gate'])
    def test_create_server_metadata_blank_key(self):
        # Blank key should trigger an error.
        meta = {'': 'data1'}
        self.assertRaises(exceptions.BadRequest,
                          self.create_test_server,
                          meta=meta)

    @test.attr(type=['negative', 'gate'])
    def test_server_metadata_non_existent_server(self):
        # GET on a non-existent server should not succeed
        non_existent_server_id = data_utils.rand_uuid()
        self.assertRaises(exceptions.NotFound,
                          self.client.get_server_metadata_item,
                          non_existent_server_id,
                          'test2')

    @test.attr(type=['negative', 'gate'])
    def test_list_server_metadata_non_existent_server(self):
        # List metadata on a non-existent server should not succeed
        non_existent_server_id = data_utils.rand_uuid()
        self.assertRaises(exceptions.NotFound,
                          self.client.list_server_metadata,
                          non_existent_server_id)

    @test.attr(type=['negative', 'gate'])
    def test_wrong_key_passed_in_body(self):
        # Raise BadRequest if key in uri does not match
        # the key passed in body.
        meta = {'testkey': 'testvalue'}
        self.assertRaises(exceptions.BadRequest,
                          self.client.set_server_metadata_item,
                          self.server_id, 'key', meta)

    @test.attr(type=['negative', 'gate'])
    def test_set_metadata_non_existent_server(self):
        # Set metadata on a non-existent server should not succeed
        non_existent_server_id = data_utils.rand_uuid()
        meta = {'meta1': 'data1'}
        self.assertRaises(exceptions.NotFound,
                          self.client.set_server_metadata,
                          non_existent_server_id,
                          meta)

    @test.attr(type=['negative', 'gate'])
    def test_update_metadata_non_existent_server(self):
        # An update should not happen for a non-existent server
        non_existent_server_id = data_utils.rand_uuid()
        meta = {'key1': 'value1', 'key2': 'value2'}
        self.assertRaises(exceptions.NotFound,
                          self.client.update_server_metadata,
                          non_existent_server_id,
                          meta)

    @test.attr(type=['negative', 'gate'])
    def test_update_metadata_with_blank_key(self):
        # Blank key should trigger an error
        meta = {'': 'data1'}
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_server_metadata,
                          self.server_id, meta=meta)

    @test.attr(type=['negative', 'gate'])
    def test_delete_metadata_non_existent_server(self):
        # Should not be able to delete metadata item from a non-existent server
        non_existent_server_id = data_utils.rand_uuid()
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_server_metadata_item,
                          non_existent_server_id,
                          'd')

    @test.attr(type=['negative', 'gate'])
    def test_metadata_items_limit(self):
        # Raise a 413 OverLimit exception while exceeding metadata items limit
        # for tenant.
        _, quota_set = self.quotas.get_quota_set(self.tenant_id)
        quota_metadata = quota_set['metadata_items']
        req_metadata = {}
        for num in range(1, quota_metadata + 2):
            req_metadata['key' + str(num)] = 'val' + str(num)
        self.assertRaises(exceptions.OverLimit,
                          self.client.set_server_metadata,
                          self.server_id, req_metadata)

        # Raise a 413 OverLimit exception while exceeding metadata items limit
        # for tenant (update).
        self.assertRaises(exceptions.OverLimit,
                          self.client.update_server_metadata,
                          self.server_id, req_metadata)

    @test.attr(type=['negative', 'gate'])
    def test_set_server_metadata_blank_key(self):
        # Raise a bad request error for blank key.
        # set_server_metadata will replace all metadata with new value
        meta = {'': 'data1'}
        self.assertRaises(exceptions.BadRequest,
                          self.client.set_server_metadata,
                          self.server_id, meta=meta)

    @test.attr(type=['negative', 'gate'])
    def test_set_server_metadata_missing_metadata(self):
        # Raise a bad request error for a missing metadata field
        # set_server_metadata will replace all metadata with new value
        meta = {'meta1': 'data1'}
        self.assertRaises(exceptions.BadRequest,
                          self.client.set_server_metadata,
                          self.server_id, meta=meta, no_metadata_field=True)
