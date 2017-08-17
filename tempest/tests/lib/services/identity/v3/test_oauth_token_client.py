# Copyright 2017 AT&T Corporation.
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

import fixtures

from tempest.lib.services.identity.v3 import oauth_token_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib import fake_http
from tempest.tests.lib.services import base


class TestOAUTHTokenClient(base.BaseServiceTest):
    FAKE_CREATE_REQUEST_TOKEN = {
        'oauth_token': '29971f',
        'oauth_token_secret': '238eb8',
        'oauth_expires_at': '2013-09-11T06:07:51.501805Z'
    }

    FAKE_AUTHORIZE_REQUEST_TOKEN = {
        'token': {
            'oauth_verifier': '8171'
        }
    }

    FAKE_CREATE_ACCESS_TOKEN = {
        'oauth_token': 'accd36',
        'oauth_token_secret': 'aa47da',
        'oauth_expires_at': '2013-09-11T06:07:51.501805Z'
    }

    FAKE_ACCESS_TOKEN_INFO = {
        'access_token': {
            'consumer_id': '7fea2d',
            'id': '6be26a',
            'expires_at': '2013-09-11T06:07:51.501805Z',
            'links': {
                'roles': 'http://example.com/identity/v3/' +
                         'users/ce9e07/OS-OAUTH1/access_tokens/6be26a/roles',
                'self': 'http://example.com/identity/v3/' +
                        'users/ce9e07/OS-OAUTH1/access_tokens/6be26a'
            },
            'project_id': 'b9fca3',
            'authorizing_user_id': 'ce9e07'
        }
    }

    FAKE_LIST_ACCESS_TOKENS = {
        'access_tokens': [
            {
                'consumer_id': '7fea2d',
                'id': '6be26a',
                'expires_at': '2013-09-11T06:07:51.501805Z',
                'links': {
                    'roles': 'http://example.com/identity/v3/' +
                             'users/ce9e07/OS-OAUTH1/access_tokens/' +
                             '6be26a/roles',
                    'self': 'http://example.com/identity/v3/' +
                            'users/ce9e07/OS-OAUTH1/access_tokens/6be26a'
                },
                'project_id': 'b9fca3',
                'authorizing_user_id': 'ce9e07'
            }
        ],
        'links': {
            'next': None,
            'previous': None,
            'self': 'http://example.com/identity/v3/' +
                    'users/ce9e07/OS-OAUTH1/access_tokens'
        }
    }

    FAKE_LIST_ACCESS_TOKEN_ROLES = {
        'roles': [
            {
                'id': '26b860',
                'domain_id': 'fake_domain',
                'links': {
                    'self': 'http://example.com/identity/v3/' +
                            'roles/26b860'
                },
                'name': 'fake_role'
            }
        ],
        'links': {
            'next': None,
            'previous': None,
            'self': 'http://example.com/identity/v3/' +
                    'users/ce9e07/OS-OAUTH1/access_tokens/6be26a/roles'
        }
    }

    FAKE_ACCESS_TOKEN_ROLE_INFO = {
        'role': {
            'id': '26b860',
            'domain_id': 'fake_domain',
            'links': {
                'self': 'http://example.com/identity/v3/' +
                        'roles/26b860'
            },
            'name': 'fake_role'
        }
    }

    def setUp(self):
        super(TestOAUTHTokenClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = oauth_token_client.OAUTHTokenClient(fake_auth,
                                                          'identity',
                                                          'regionOne')

    def _mock_token_response(self, body):
        temp_response = [key + '=' + value for key, value in body.items()]
        return '&'.join(temp_response)

    def _test_authorize_request_token(self, bytes_body=False):
        self.check_service_client_function(
            self.client.authorize_request_token,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_AUTHORIZE_REQUEST_TOKEN,
            bytes_body,
            request_token_id=self.FAKE_CREATE_REQUEST_TOKEN['oauth_token'],
            role_ids=['26b860'],
            status=200)

    def test_create_request_token(self):
        mock_resp = self._mock_token_response(self.FAKE_CREATE_REQUEST_TOKEN)
        resp = fake_http.fake_http_response(None, status=201), mock_resp
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.rest_client.RestClient.post',
            return_value=resp))

        resp = self.client.create_request_token(
            consumer_key='12345',
            consumer_secret='23456',
            project_id='c8f58432c6f00162f04d3250f')
        self.assertEqual(self.FAKE_CREATE_REQUEST_TOKEN, resp)

    def test_authorize_token_request_with_str_body(self):
        self._test_authorize_request_token()

    def test_authorize_token_request_with_bytes_body(self):
        self._test_authorize_request_token(bytes_body=True)

    def test_create_access_token(self):
        mock_resp = self._mock_token_response(self.FAKE_CREATE_ACCESS_TOKEN)
        req_secret = self.FAKE_CREATE_REQUEST_TOKEN['oauth_token_secret']
        resp = fake_http.fake_http_response(None, status=201), mock_resp
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.rest_client.RestClient.post',
            return_value=resp))

        resp = self.client.create_access_token(
            consumer_key='12345',
            consumer_secret='23456',
            request_key=self.FAKE_CREATE_REQUEST_TOKEN['oauth_token'],
            request_secret=req_secret,
            oauth_verifier='8171')
        self.assertEqual(self.FAKE_CREATE_ACCESS_TOKEN, resp)

    def test_get_access_token(self):
        self.check_service_client_function(
            self.client.get_access_token,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ACCESS_TOKEN_INFO,
            user_id='ce9e07',
            access_token_id=self.FAKE_ACCESS_TOKEN_INFO['access_token']['id'],
            status=200)

    def test_list_access_tokens(self):
        self.check_service_client_function(
            self.client.list_access_tokens,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ACCESS_TOKENS,
            user_id='ce9e07',
            status=200)

    def test_revoke_access_token(self):
        self.check_service_client_function(
            self.client.revoke_access_token,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            user_id=self.FAKE_ACCESS_TOKEN_INFO['access_token']['consumer_id'],
            access_token_id=self.FAKE_ACCESS_TOKEN_INFO['access_token']['id'],
            status=204)

    def test_list_access_token_roles(self):
        self.check_service_client_function(
            self.client.list_access_token_roles,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_ACCESS_TOKEN_ROLES,
            user_id='ce9e07',
            access_token_id=self.FAKE_ACCESS_TOKEN_INFO['access_token']['id'],
            status=200)

    def test_get_access_token_role(self):
        self.check_service_client_function(
            self.client.get_access_token_role,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ACCESS_TOKEN_ROLE_INFO,
            user_id='ce9e07',
            access_token_id=self.FAKE_ACCESS_TOKEN_INFO['access_token']['id'],
            role_id=self.FAKE_ACCESS_TOKEN_ROLE_INFO['role']['id'],
            status=200)
