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

import json

import httplib2
from oslotest import mockpatch

from tempest.lib.common import rest_client
from tempest.lib import exceptions
from tempest.lib.services.identity.v3 import token_client
from tempest.tests.lib import base
from tempest.tests.lib import fake_http


class TestTokenClientV2(base.TestCase):

    def setUp(self):
        super(TestTokenClientV2, self).setUp()
        self.fake_201_http = fake_http.fake_httplib2(return_type=201)

    def test_init_without_authurl(self):
        self.assertRaises(exceptions.IdentityError,
                          token_client.V3TokenClient, None)

    def test_auth(self):
        token_client_v3 = token_client.V3TokenClient('fake_url')
        post_mock = self.useFixture(mockpatch.PatchObject(
            token_client_v3, 'post', return_value=self.fake_201_http.request(
                'fake_url', body={'access': {'token': 'fake_token'}})))
        resp = token_client_v3.auth(username='fake_user', password='fake_pass')
        self.assertIsInstance(resp, rest_client.ResponseBody)
        req_dict = json.dumps({
            'auth': {
                'identity': {
                    'methods': ['password'],
                    'password': {
                        'user': {
                            'name': 'fake_user',
                            'password': 'fake_pass',
                        }
                    }
                },
            }
        }, sort_keys=True)
        post_mock.mock.assert_called_once_with('fake_url/auth/tokens',
                                               body=req_dict)

    def test_auth_with_project_id_and_domain_id(self):
        token_client_v3 = token_client.V3TokenClient('fake_url')
        post_mock = self.useFixture(mockpatch.PatchObject(
            token_client_v3, 'post', return_value=self.fake_201_http.request(
                'fake_url', body={'access': {'token': 'fake_token'}})))
        resp = token_client_v3.auth(
            username='fake_user', password='fake_pass',
            project_id='fcac2a055a294e4c82d0a9c21c620eb4',
            user_domain_id='14f4a9a99973404d8c20ba1d2af163ff',
            project_domain_id='291f63ae9ac54ee292ca09e5f72d9676')
        self.assertIsInstance(resp, rest_client.ResponseBody)
        req_dict = json.dumps({
            'auth': {
                'identity': {
                    'methods': ['password'],
                    'password': {
                        'user': {
                            'name': 'fake_user',
                            'password': 'fake_pass',
                            'domain': {
                                'id': '14f4a9a99973404d8c20ba1d2af163ff'
                            }
                        }
                    }
                },
                'scope': {
                    'project': {
                        'id': 'fcac2a055a294e4c82d0a9c21c620eb4',
                        'domain': {
                            'id': '291f63ae9ac54ee292ca09e5f72d9676'
                        }
                    }
                }
            }
        }, sort_keys=True)
        post_mock.mock.assert_called_once_with('fake_url/auth/tokens',
                                               body=req_dict)

    def test_auth_with_tenant(self):
        token_client_v2 = token_client.V3TokenClient('fake_url')
        post_mock = self.useFixture(mockpatch.PatchObject(
            token_client_v2, 'post', return_value=self.fake_201_http.request(
                'fake_url', body={'access': {'token': 'fake_token'}})))
        resp = token_client_v2.auth(username='fake_user', password='fake_pass',
                                    project_name='fake_tenant')
        self.assertIsInstance(resp, rest_client.ResponseBody)
        req_dict = json.dumps({
            'auth': {
                'identity': {
                    'methods': ['password'],
                    'password': {
                        'user': {
                            'name': 'fake_user',
                            'password': 'fake_pass',
                        }
                    }},
                'scope': {
                    'project': {
                        'name': 'fake_tenant'
                    }
                },
            }
        }, sort_keys=True)

        post_mock.mock.assert_called_once_with('fake_url/auth/tokens',
                                               body=req_dict)

    def test_request_with_str_body(self):
        token_client_v3 = token_client.V3TokenClient('fake_url')
        self.useFixture(mockpatch.PatchObject(
            token_client_v3, 'raw_request', return_value=(
                httplib2.Response({"status": "200"}),
                str('{"access": {"token": "fake_token"}}'))))
        resp, body = token_client_v3.request('GET', 'fake_uri')
        self.assertIsInstance(resp, httplib2.Response)
        self.assertIsInstance(body, dict)

    def test_request_with_bytes_body(self):
        token_client_v3 = token_client.V3TokenClient('fake_url')
        self.useFixture(mockpatch.PatchObject(
            token_client_v3, 'raw_request', return_value=(
                httplib2.Response({"status": "200"}),
                bytes(b'{"access": {"token": "fake_token"}}'))))
        resp, body = token_client_v3.request('GET', 'fake_uri')
        self.assertIsInstance(resp, httplib2.Response)
        self.assertIsInstance(body, dict)
