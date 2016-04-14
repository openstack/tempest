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

import mock

from tempest.lib.common import rest_client
from tempest.lib import exceptions
from tempest.lib.services.compute import base_compute_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib import fake_http
from tempest.tests.lib.services.compute import base


class TestMicroversionHeaderCheck(base.BaseComputeServiceTest):

    def setUp(self):
        super(TestMicroversionHeaderCheck, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = base_compute_client.BaseComputeClient(
            fake_auth, 'compute', 'regionOne')
        base_compute_client.COMPUTE_MICROVERSION = '2.2'

    def tearDown(self):
        super(TestMicroversionHeaderCheck, self).tearDown()
        base_compute_client.COMPUTE_MICROVERSION = None

    @mock.patch('tempest.lib.common.http.ClosingHttp.request')
    def test_correct_microverion_in_response(self, mock_request):
        response = fake_http.fake_http_response(
            headers={self.client.api_microversion_header_name: '2.2'},
        )
        mock_request.return_value = response, ''
        self.client.get('fake_url')

    @mock.patch('tempest.lib.common.http.ClosingHttp.request')
    def test_incorrect_microverion_in_response(self, mock_request):
        response = fake_http.fake_http_response(
            headers={self.client.api_microversion_header_name: '2.3'},
        )
        mock_request.return_value = response, ''
        self.assertRaises(exceptions.InvalidHTTPResponseHeader,
                          self.client.get, 'fake_url')

    @mock.patch('tempest.lib.common.http.ClosingHttp.request')
    def test_no_microverion_header_in_response(self, mock_request):
        response = fake_http.fake_http_response(
            headers={},
        )
        mock_request.return_value = response, ''
        self.assertRaises(exceptions.InvalidHTTPResponseHeader,
                          self.client.get, 'fake_url')


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
        base_compute_client.COMPUTE_MICROVERSION = self.api_microversion

    def tearDown(self):
        super(TestSchemaVersionsNone, self).tearDown()
        base_compute_client.COMPUTE_MICROVERSION = None

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
        base_compute_client.COMPUTE_MICROVERSION = self.api_microversion

    def tearDown(self):
        super(TestSchemaVersionsNotFound, self).tearDown()
        base_compute_client.COMPUTE_MICROVERSION = None

    def test_schema(self):
        self.assertRaises(exceptions.JSONSchemaNotFound,
                          self.client.return_selected_schema)


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
            return (fake_http.fake_http_response({}, status=200), '')

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
        base_compute_client.COMPUTE_MICROVERSION = '2.2'

    def tearDown(self):
        super(TestClientWithMicroversionHeader, self).tearDown()
        base_compute_client.COMPUTE_MICROVERSION = None

    def test_microverion_header(self):
        header = self.client.get_headers()
        self.assertIn('X-OpenStack-Nova-API-Version', header)
        self.assertEqual('2.2',
                         header['X-OpenStack-Nova-API-Version'])

    def test_microverion_header_in_raw_request(self):
        def raw_request(*args, **kwargs):
            self.assertIn('X-OpenStack-Nova-API-Version', kwargs['headers'])
            self.assertEqual('2.2',
                             kwargs['headers']['X-OpenStack-Nova-API-Version'])
            return (fake_http.fake_http_response(
                headers={self.client.api_microversion_header_name: '2.2'},
                status=200), '')

        with mock.patch.object(rest_client.RestClient,
                               'raw_request') as mock_get:
            mock_get.side_effect = raw_request
            self.client.get('fake_url')
