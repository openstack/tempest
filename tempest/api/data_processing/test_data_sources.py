# Copyright (c) 2014 Mirantis Inc.
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

from tempest.api.data_processing import base as dp_base
from tempest import test


class DataSourceTest(dp_base.BaseDataProcessingTest):
    @classmethod
    def resource_setup(cls):
        super(DataSourceTest, cls).resource_setup()
        cls.swift_data_source_with_creds = {
            'url': 'swift://sahara-container.sahara/input-source',
            'description': 'Test data source',
            'credentials': {
                'user': cls.os.credentials.username,
                'password': cls.os.credentials.password
            },
            'type': 'swift'
        }
        cls.swift_data_source = cls.swift_data_source_with_creds.copy()
        del cls.swift_data_source['credentials']

        cls.local_hdfs_data_source = {
            'url': 'input-source',
            'description': 'Test data source',
            'type': 'hdfs'
        }

        cls.external_hdfs_data_source = {
            'url': 'hdfs://172.18.168.2:8020/usr/hadoop/input-source',
            'description': 'Test data source',
            'type': 'hdfs'
        }

    def _create_data_source(self, source_body, source_name=None):
        """Creates Data Source with optional name specified.

        It creates a link to input-source file (it may not exist), ensures
        source name and response body. Returns id and name of created source.
        """
        if not source_name:
            # generate random name if it's not specified
            source_name = data_utils.rand_name('sahara-data-source')

        # create data source
        resp_body = self.create_data_source(source_name, **source_body)

        # ensure that source created successfully
        self.assertEqual(source_name, resp_body['name'])
        if source_body['type'] == 'swift':
            source_body = self.swift_data_source
        self.assertDictContainsSubset(source_body, resp_body)

        return resp_body['id'], source_name

    def _list_data_sources(self, source_info):
        # check for data source in list
        sources = self.client.list_data_sources()
        sources_info = [(source['id'], source['name']) for source in sources]
        self.assertIn(source_info, sources_info)

    def _get_data_source(self, source_id, source_name, source_body):
        # check data source fetch by id
        source = self.client.get_data_source(source_id)
        self.assertEqual(source_name, source['name'])
        self.assertDictContainsSubset(source_body, source)

    @test.attr(type='smoke')
    @test.idempotent_id('9e0e836d-c372-4fca-91b7-b66c3e9646c8')
    def test_swift_data_source_create(self):
        self._create_data_source(self.swift_data_source_with_creds)

    @test.attr(type='smoke')
    @test.idempotent_id('3cb87a4a-0534-4b97-9edc-8bbc822b68a0')
    def test_swift_data_source_list(self):
        source_info = (
            self._create_data_source(self.swift_data_source_with_creds))
        self._list_data_sources(source_info)

    @test.attr(type='smoke')
    @test.idempotent_id('fc07409b-6477-4cb3-9168-e633c46b227f')
    def test_swift_data_source_get(self):
        source_id, source_name = (
            self._create_data_source(self.swift_data_source_with_creds))
        self._get_data_source(source_id, source_name, self.swift_data_source)

    @test.attr(type='smoke')
    @test.idempotent_id('df53669c-0cd1-4cf7-b408-4cf215d8beb8')
    def test_swift_data_source_delete(self):
        source_id, _ = (
            self._create_data_source(self.swift_data_source_with_creds))

        # delete the data source by id
        self.client.delete_data_source(source_id)

    @test.attr(type='smoke')
    @test.idempotent_id('88505d52-db01-4229-8f1d-a1137da5fe2d')
    def test_local_hdfs_data_source_create(self):
        self._create_data_source(self.local_hdfs_data_source)

    @test.attr(type='smoke')
    @test.idempotent_id('81d7d42a-d7f6-4d9b-b38c-0801a4dfe3c2')
    def test_local_hdfs_data_source_list(self):
        source_info = self._create_data_source(self.local_hdfs_data_source)
        self._list_data_sources(source_info)

    @test.attr(type='smoke')
    @test.idempotent_id('ec0144c6-db1e-4169-bb06-7abae14a8443')
    def test_local_hdfs_data_source_get(self):
        source_id, source_name = (
            self._create_data_source(self.local_hdfs_data_source))
        self._get_data_source(
            source_id, source_name, self.local_hdfs_data_source)

    @test.attr(type='smoke')
    @test.idempotent_id('e398308b-4230-4f86-ba10-9b0b60a59c8d')
    def test_local_hdfs_data_source_delete(self):
        source_id, _ = self._create_data_source(self.local_hdfs_data_source)

        # delete the data source by id
        self.client.delete_data_source(source_id)

    @test.attr(type='smoke')
    @test.idempotent_id('bfd91128-e642-4d95-a973-3e536962180c')
    def test_external_hdfs_data_source_create(self):
        self._create_data_source(self.external_hdfs_data_source)

    @test.attr(type='smoke')
    @test.idempotent_id('92e2be72-f7ab-499d-ae01-fb9943c90d8e')
    def test_external_hdfs_data_source_list(self):
        source_info = self._create_data_source(self.external_hdfs_data_source)
        self._list_data_sources(source_info)

    @test.attr(type='smoke')
    @test.idempotent_id('a31edb1b-6bc6-4f42-871f-70cd243184ac')
    def test_external_hdfs_data_source_get(self):
        source_id, source_name = (
            self._create_data_source(self.external_hdfs_data_source))
        self._get_data_source(
            source_id, source_name, self.external_hdfs_data_source)

    @test.attr(type='smoke')
    @test.idempotent_id('295924cd-a085-4b45-aea8-0707cdb2da7e')
    def test_external_hdfs_data_source_delete(self):
        source_id, _ = self._create_data_source(self.external_hdfs_data_source)

        # delete the data source by id
        self.client.delete_data_source(source_id)
