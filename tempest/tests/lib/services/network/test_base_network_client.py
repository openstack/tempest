# Copyright 2017 AT&T Corporation.
# All rights reserved.
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

from tempest.lib.services.network import base as base_network_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib import fake_http
from tempest.tests.lib.services import base


class TestBaseNetworkClient(base.BaseServiceTest):

    def setUp(self):
        super(TestBaseNetworkClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = base_network_client.BaseNetworkClient(
            fake_auth, 'compute', 'regionOne')

        self.mock_expected_success = mock.patch.object(
            self.client, 'expected_success').start()

    def _assert_empty(self, resp):
        self.assertEqual([], list(resp.keys()))

    @mock.patch('tempest.lib.common.rest_client.RestClient.post')
    def test_create_resource(self, mock_post):
        response = fake_http.fake_http_response(headers=None, status=201)
        mock_post.return_value = response, '{"baz": "qux"}'

        post_data = {'foo': 'bar'}
        resp = self.client.create_resource('/fake_url', post_data)

        self.assertEqual({'status': '201'}, resp.response)
        self.assertEqual("qux", resp["baz"])
        mock_post.assert_called_once_with('v2.0/fake_url', '{"foo": "bar"}')
        self.mock_expected_success.assert_called_once_with(
            201, 201)

    @mock.patch('tempest.lib.common.rest_client.RestClient.post')
    def test_create_resource_expect_different_values(self, mock_post):
        response = fake_http.fake_http_response(headers=None, status=200)
        mock_post.return_value = response, '{}'

        post_data = {'foo': 'bar'}
        resp = self.client.create_resource('/fake_url', post_data,
                                           expect_response_code=200,
                                           expect_empty_body=True)

        self.assertEqual({'status': '200'}, resp.response)
        self._assert_empty(resp)
        mock_post.assert_called_once_with('v2.0/fake_url', '{"foo": "bar"}')
        self.mock_expected_success.assert_called_once_with(
            200, 200)

    @mock.patch('tempest.lib.common.rest_client.RestClient.put')
    def test_update_resource(self, mock_put):
        response = fake_http.fake_http_response(headers=None, status=200)
        mock_put.return_value = response, '{"baz": "qux"}'

        put_data = {'foo': 'bar'}
        resp = self.client.update_resource('/fake_url', put_data)

        self.assertEqual({'status': '200'}, resp.response)
        self.assertEqual("qux", resp["baz"])
        mock_put.assert_called_once_with('v2.0/fake_url', '{"foo": "bar"}')
        self.mock_expected_success.assert_called_once_with(
            200, 200)

    @mock.patch('tempest.lib.common.rest_client.RestClient.put')
    def test_update_resource_expect_different_values(self, mock_put):
        response = fake_http.fake_http_response(headers=None, status=201)
        mock_put.return_value = response, '{}'

        put_data = {'foo': 'bar'}
        resp = self.client.update_resource('/fake_url', put_data,
                                           expect_response_code=201,
                                           expect_empty_body=True)

        self.assertEqual({'status': '201'}, resp.response)
        self._assert_empty(resp)
        mock_put.assert_called_once_with('v2.0/fake_url', '{"foo": "bar"}')
        self.mock_expected_success.assert_called_once_with(
            201, 201)
