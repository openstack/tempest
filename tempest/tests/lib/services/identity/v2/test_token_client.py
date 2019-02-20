# Copyright 2015 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import mock
from oslo_serialization import jsonutils as json

from tempest.lib.common import rest_client
from tempest.lib import exceptions
from tempest.lib.services.identity.v2 import token_client
from tempest.tests import base
from tempest.tests.lib import fake_http


class TestTokenClientV2(base.TestCase):

    def test_init_without_authurl(self):
        self.assertRaises(exceptions.IdentityError,
                          token_client.TokenClient, None)

    def test_auth(self):
        token_client_v2 = token_client.TokenClient('fake_url')
        response = fake_http.fake_http_response(
            None, status=200,
        )
        body = {'access': {'token': 'fake_token'}}

        with mock.patch.object(token_client_v2, 'post') as post_mock:
            post_mock.return_value = response, body
            resp = token_client_v2.auth('fake_user', 'fake_pass')

        self.assertIsInstance(resp, rest_client.ResponseBody)
        req_dict = json.dumps({
            'auth': {
                'passwordCredentials': {
                    'username': 'fake_user',
                    'password': 'fake_pass',
                },
            }
        }, sort_keys=True)
        post_mock.assert_called_once_with('fake_url/tokens',
                                          body=req_dict)

    def test_auth_with_tenant(self):
        token_client_v2 = token_client.TokenClient('fake_url')
        response = fake_http.fake_http_response(
            None, status=200,
        )
        body = {'access': {'token': 'fake_token'}}

        with mock.patch.object(token_client_v2, 'post') as post_mock:
            post_mock.return_value = response, body
            resp = token_client_v2.auth('fake_user', 'fake_pass',
                                        'fake_tenant')

        self.assertIsInstance(resp, rest_client.ResponseBody)
        req_dict = json.dumps({
            'auth': {
                'tenantName': 'fake_tenant',
                'passwordCredentials': {
                    'username': 'fake_user',
                    'password': 'fake_pass',
                },
            }
        }, sort_keys=True)
        post_mock.assert_called_once_with('fake_url/tokens',
                                          body=req_dict)

    def test_request_with_str_body(self):
        token_client_v2 = token_client.TokenClient('fake_url')
        response = fake_http.fake_http_response(
            None, status=200,
        )
        body = str('{"access": {"token": "fake_token"}}')

        with mock.patch.object(token_client_v2, 'raw_request') as mock_raw_r:
            mock_raw_r.return_value = response, body
            resp, body = token_client_v2.request('GET', 'fake_uri')
        self.assertIsInstance(body, dict)

    def test_request_with_bytes_body(self):
        token_client_v2 = token_client.TokenClient('fake_url')

        response = fake_http.fake_http_response(
            None, status=200,
        )
        body = b'{"access": {"token": "fake_token"}}'

        with mock.patch.object(token_client_v2, 'raw_request') as mock_raw_r:
            mock_raw_r.return_value = response, body
            resp, body = token_client_v2.request('GET', 'fake_uri')

        self.assertIsInstance(body, dict)
