# Copyright 2015 NEC Corporation.  All rights reserved.
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

import httplib2
import mock
from tempest_lib.common import rest_client

from tempest import exceptions
from tempest.services.compute.json import base as base_compute_client
from tempest.tests import fake_auth_provider
from tempest.tests.services.compute import base


class TestClientWithoutMicroversionHeader(base.BaseComputeServiceTest):

    def setUp(self):
        super(TestClientWithoutMicroversionHeader, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = base_compute_client.BaseComputeClient(
            fake_auth, 'compute', 'regionOne')

    def test_no_microverion_header(self):
        header = self.client.get_headers()
        self.assertNotIn('X-OpenStack-Nova-API-Version', header)

    def test_no_microverion_header_in_raw_request(self):
        def raw_request(*args, **kwargs):
            self.assertNotIn('X-OpenStack-Nova-API-Version', kwargs['headers'])
            return (httplib2.Response({'status': 200}), {})

        with mock.patch.object(rest_client.RestClient,
                               'raw_request') as mock_get:
            mock_get.side_effect = raw_request
            self.client.get('fake_url')


class TestClientWithMicroversionHeader(base.BaseComputeServiceTest):

    def setUp(self):
        super(TestClientWithMicroversionHeader, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = base_compute_client.BaseComputeClient(
            fake_auth, 'compute', 'regionOne')
        self.client.api_microversion = '2.2'

    def test_microverion_header(self):
        header = self.client.get_headers()
        self.assertIn('X-OpenStack-Nova-API-Version', header)
        self.assertEqual(self.client.api_microversion,
                         header['X-OpenStack-Nova-API-Version'])

    def test_microverion_header_in_raw_request(self):
        def raw_request(*args, **kwargs):
            self.assertIn('X-OpenStack-Nova-API-Version', kwargs['headers'])
            self.assertEqual(self.client.api_microversion,
                             kwargs['headers']['X-OpenStack-Nova-API-Version'])
            return (httplib2.Response({'status': 200}), {})

        with mock.patch.object(rest_client.RestClient,
                               'raw_request') as mock_get:
            mock_get.side_effect = raw_request
            self.client.get('fake_url')


class DummyServiceClient1(base_compute_client.BaseComputeClient):
    schema_versions_info = [
        {'min': None, 'max': '2.1', 'schema': 'schemav21'},
        {'min': '2.2', 'max': '2.9', 'schema': 'schemav22'},
        {'min': '2.10', 'max': None, 'schema': 'schemav210'}]

    def return_selected_schema(self):
        return self.get_schema(self.schema_versions_info)


class TestSchemaVersionsNone(base.BaseComputeServiceTest):
    api_microversion = None
    expected_schema = 'schemav21'

    def setUp(self):
        super(TestSchemaVersionsNone, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = DummyServiceClient1(fake_auth, 'compute', 'regionOne')
        self.client.api_microversion = self.api_microversion

    def test_schema(self):
        self.assertEqual(self.expected_schema,
                         self.client.return_selected_schema())


class TestSchemaVersionsV21(TestSchemaVersionsNone):
    api_microversion = '2.1'
    expected_schema = 'schemav21'


class TestSchemaVersionsV22(TestSchemaVersionsNone):
    api_microversion = '2.2'
    expected_schema = 'schemav22'


class TestSchemaVersionsV25(TestSchemaVersionsNone):
    api_microversion = '2.5'
    expected_schema = 'schemav22'


class TestSchemaVersionsV29(TestSchemaVersionsNone):
    api_microversion = '2.9'
    expected_schema = 'schemav22'


class TestSchemaVersionsV210(TestSchemaVersionsNone):
    api_microversion = '2.10'
    expected_schema = 'schemav210'


class TestSchemaVersionsLatest(TestSchemaVersionsNone):
    api_microversion = 'latest'
    expected_schema = 'schemav210'


class DummyServiceClient2(base_compute_client.BaseComputeClient):
    schema_versions_info = [
        {'min': None, 'max': '2.1', 'schema': 'schemav21'},
        {'min': '2.2', 'max': '2.9', 'schema': 'schemav22'}]

    def return_selected_schema(self):
        return self.get_schema(self.schema_versions_info)


class TestSchemaVersionsNotFound(base.BaseComputeServiceTest):
    api_microversion = '2.10'
    expected_schema = 'schemav210'

    def setUp(self):
        super(TestSchemaVersionsNotFound, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = DummyServiceClient2(fake_auth, 'compute', 'regionOne')
        self.client.api_microversion = self.api_microversion

    def test_schema(self):
        self.assertRaises(exceptions.JSONSchemaNotFound,
                          self.client.return_selected_schema)
