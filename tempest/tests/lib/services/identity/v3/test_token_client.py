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
from tempest.lib.services.identity.v3 import token_client
from tempest.tests import base
from tempest.tests.lib import fake_identity


class TestTokenClientV3(base.TestCase):

    def test_init_without_authurl(self):
        self.assertRaises(exceptions.IdentityError,
                          token_client.V3TokenClient, None)

    def test_auth(self):
        token_client_v3 = token_client.V3TokenClient('fake_url')
        response, body_text = fake_identity._fake_v3_response(None, None)
        body = json.loads(body_text)

        with mock.patch.object(token_client_v3, 'post') as post_mock:
            post_mock.return_value = response, body
            resp = token_client_v3.auth(username='fake_user',
                                        password='fake_pass')

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
        post_mock.assert_called_once_with('fake_url/auth/tokens',
                                          body=req_dict)

    def test_auth_with_project_id_and_domain_id(self):
        token_client_v3 = token_client.V3TokenClient('fake_url')
        response, body_text = fake_identity._fake_v3_response(None, None)
        body = json.loads(body_text)

        with mock.patch.object(token_client_v3, 'post') as post_mock:
            post_mock.return_value = response, body
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
        post_mock.assert_called_once_with('fake_url/auth/tokens',
                                          body=req_dict)

    def test_auth_with_tenant(self):
        token_client_v3 = token_client.V3TokenClient('fake_url')
        response, body_text = fake_identity._fake_v3_response(None, None)
        body = json.loads(body_text)

        with mock.patch.object(token_client_v3, 'post') as post_mock:
            post_mock.return_value = response, body
            resp = token_client_v3.auth(username='fake_user',
                                        password='fake_pass',
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

        post_mock.assert_called_once_with('fake_url/auth/tokens',
                                          body=req_dict)

    def test_request_with_str_body(self):
        token_client_v3 = token_client.V3TokenClient('fake_url')

        with mock.patch.object(token_client_v3, 'raw_request') as mock_raw_r:
            mock_raw_r.return_value = (
                fake_identity._fake_v3_response(None, None))
            resp, body = token_client_v3.request('GET', 'fake_uri')

        self.assertIsInstance(body, dict)

    def test_request_with_bytes_body(self):
        token_client_v3 = token_client.V3TokenClient('fake_url')

        response, body_text = fake_identity._fake_v3_response(None, None)
        body = body_text.encode('utf-8')

        with mock.patch.object(token_client_v3, 'raw_request') as mock_raw_r:
            mock_raw_r.return_value = response, body
            resp, body = token_client_v3.request('GET', 'fake_uri')

        self.assertIsInstance(body, dict)
