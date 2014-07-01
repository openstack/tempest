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

from tempest.api.data_processing import base as dp_base
from tempest.common.utils import data_utils
from tempest import test


class DataSourceTest(dp_base.BaseDataProcessingTest):
    @classmethod
    def setUpClass(cls):
        super(DataSourceTest, cls).setUpClass()
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

        It creates a link to input-source file (it may not exist) and ensures
        response status and source name. Returns id and name of created source.
        """
        if not source_name:
            # generate random name if it's not specified
            source_name = data_utils.rand_name('sahara-data-source')

        # create data source
        resp, body = self.create_data_source(source_name, **source_body)

        # ensure that source created successfully
        self.assertEqual(202, resp.status)
        self.assertEqual(source_name, body['name'])
        if source_body['type'] == 'swift':
            source_body = self.swift_data_source
        self.assertDictContainsSubset(source_body, body)

        return body['id'], source_name

    def _list_data_sources(self, source_info):
        # check for data source in list
        resp, sources = self.client.list_data_sources()
        self.assertEqual(200, resp.status)
        sources_info = [(source['id'], source['name']) for source in sources]
        self.assertIn(source_info, sources_info)

    def _get_data_source(self, source_id, source_name, source_body):
        # check data source fetch by id
        resp, source = self.client.get_data_source(source_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(source_name, source['name'])
        self.assertDictContainsSubset(source_body, source)

    def _delete_data_source(self, source_id):
        # delete the data source by id
        resp = self.client.delete_data_source(source_id)[0]
        self.assertEqual(204, resp.status)

    @test.attr(type='smoke')
    def test_swift_data_source_create(self):
        self._create_data_source(self.swift_data_source_with_creds)

    @test.attr(type='smoke')
    def test_swift_data_source_list(self):
        source_info = self._create_data_source(
            self.swift_data_source_with_creds)
        self._list_data_sources(source_info)

    @test.attr(type='smoke')
    def test_swift_data_source_get(self):
        source_id, source_name = self._create_data_source(
            self.swift_data_source_with_creds)
        self._get_data_source(source_id, source_name, self.swift_data_source)

    @test.attr(type='smoke')
    def test_swift_data_source_delete(self):
        source_id = self._create_data_source(
            self.swift_data_source_with_creds)[0]
        self._delete_data_source(source_id)

    @test.attr(type='smoke')
    def test_local_hdfs_data_source_create(self):
        self._create_data_source(self.local_hdfs_data_source)

    @test.attr(type='smoke')
    def test_local_hdfs_data_source_list(self):
        source_info = self._create_data_source(self.local_hdfs_data_source)
        self._list_data_sources(source_info)

    @test.attr(type='smoke')
    def test_local_hdfs_data_source_get(self):
        source_id, source_name = self._create_data_source(
            self.local_hdfs_data_source)
        self._get_data_source(
            source_id, source_name, self.local_hdfs_data_source)

    @test.attr(type='smoke')
    def test_local_hdfs_data_source_delete(self):
        source_id = self._create_data_source(self.local_hdfs_data_source)[0]
        self._delete_data_source(source_id)

    @test.attr(type='smoke')
    def test_external_hdfs_data_source_create(self):
        self._create_data_source(self.external_hdfs_data_source)

    @test.attr(type='smoke')
    def test_external_hdfs_data_source_list(self):
        source_info = self._create_data_source(self.external_hdfs_data_source)
        self._list_data_sources(source_info)

    @test.attr(type='smoke')
    def test_external_hdfs_data_source_get(self):
        source_id, source_name = self._create_data_source(
            self.external_hdfs_data_source)
        self._get_data_source(
            source_id, source_name, self.external_hdfs_data_source)

    @test.attr(type='smoke')
    def test_external_hdfs_data_source_delete(self):
        source_id = self._create_data_source(self.external_hdfs_data_source)[0]
        self._delete_data_source(source_id)
