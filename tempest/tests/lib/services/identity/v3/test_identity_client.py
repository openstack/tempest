# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.identity.v3 import identity_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestIdentityClient(base.BaseServiceTest):
    FAKE_TOKEN = {
        "tokens": {
            "id": "cbc36478b0bd8e67e89",
            "name": "FakeToken",
            "type": "token",
        }
    }

    FAKE_API_INFO = {
        "name": "API_info",
        "type": "API",
        "description": "test_description"
    }

    FAKE_AUTH_PROJECTS = {
        "projects": [
            {
                "domain_id": "1789d1",
                "enabled": True,
                "id": "263fd9",
                "links": {
                    "self": "https://example.com/identity/v3/projects/263fd9"
                },
                "name": "Test Group"
            },
            {
                "domain_id": "1789d1",
                "enabled": True,
                "id": "50ef01",
                "links": {
                    "self": "https://example.com/identity/v3/projects/50ef01"
                },
                "name": "Build Group"
            }
        ],
        "links": {
            "self": "https://example.com/identity/v3/auth/projects",
            "previous": None,
            "next": None
        }
    }

    FAKE_AUTH_DOMAINS = {
        "domains": [
            {
                "description": "my domain description",
                "enabled": True,
                "id": "1789d1",
                "links": {
                    "self": "https://example.com/identity/v3/domains/1789d1"
                },
                "name": "my domain"
            },
            {
                "description": "description of my other domain",
                "enabled": True,
                "id": "43e8da",
                "links": {
                    "self": "https://example.com/identity/v3/domains/43e8da"
                },
                "name": "another domain"
            }
        ],
        "links": {
            "self": "https://example.com/identity/v3/auth/domains",
            "previous": None,
            "next": None
        }
    }

    def setUp(self):
        super(TestIdentityClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = identity_client.IdentityClient(fake_auth,
                                                     'identity',
                                                     'regionOne')

    def _test_show_api_description(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_api_description,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_API_INFO,
            bytes_body)

    def _test_show_token(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_token,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_TOKEN,
            bytes_body,
            resp_token="cbc36478b0bd8e67e89")

    def _test_list_auth_projects(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_auth_projects,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_AUTH_PROJECTS,
            bytes_body)

    def _test_list_auth_domains(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_auth_domains,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_AUTH_DOMAINS,
            bytes_body)

    def test_show_api_description_with_str_body(self):
        self._test_show_api_description()

    def test_show_api_description_with_bytes_body(self):
        self._test_show_api_description(bytes_body=True)

    def test_show_token_with_str_body(self):
        self._test_show_token()

    def test_show_token_with_bytes_body(self):
        self._test_show_token(bytes_body=True)

    def test_delete_token(self):
        self.check_service_client_function(
            self.client.delete_token,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            resp_token="cbc36478b0bd8e67e89",
            status=204)

    def test_check_token_existence(self):
        self.check_service_client_function(
            self.client.check_token_existence,
            'tempest.lib.common.rest_client.RestClient.head',
            {},
            resp_token="cbc36478b0bd8e67e89",
            status=200)

    def test_list_auth_projects_with_str_body(self):
        self._test_list_auth_projects()

    def test_list_auth_projects_with_bytes_body(self):
        self._test_list_auth_projects(bytes_body=True)

    def test_list_auth_domains_with_str_body(self):
        self._test_list_auth_domains()

    def test_list_auth_domains_with_bytes_body(self):
        self._test_list_auth_domains(bytes_body=True)
