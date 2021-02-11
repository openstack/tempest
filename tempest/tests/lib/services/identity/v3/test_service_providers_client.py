# Copyright 2020 Samsung Electronics Co., Ltd
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

from tempest.lib.services.identity.v3 import service_providers_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestServiceProvidersClient(base.BaseServiceTest):
    FAKE_SERVICE_PROVIDER_INFO = {
        "service_provider": {
            "auth_url": "https://example.com/identity/v3/OS-FEDERATION/" +
                        "identity_providers/FAKE_ID/protocols/fake_id1/auth",
            "description": "Fake Service Provider",
            "enabled": True,
            "id": "FAKE_ID",
            "links": {
                "self": "https://example.com/identity/v3/OS-FEDERATION/" +
                        "service_providers/FAKE_ID"
            },
            "relay_state_prefix": "ss:mem:",
            "sp_url": "https://example.com/identity/Shibboleth.sso/" +
                      "FAKE_ID1/ECP"
        }
    }

    FAKE_SERVICE_PROVIDERS_INFO = {
        "links": {
            "next": None,
            "previous": None,
            "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                    "service_providers"
        },
        "service_providers": [
            {
                "auth_url": "https://example.com/identity/v3/OS-FEDERATION/" +
                            "identity_providers/acme/protocols/saml2/auth",
                "description": "Stores ACME identities",
                "enabled": True,
                "id": "ACME",
                "links": {
                    "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                            "service_providers/ACME"
                },
                "relay_state_prefix": "ss:mem:",
                "sp_url": "https://example.com/identity/Shibboleth.sso/" +
                          "SAML2/ECP"
            },
            {
                "auth_url": "https://other.example.com/identity/v3/" +
                            "OS-FEDERATION/identity_providers/acme/" +
                            "protocols/saml2/auth",
                "description": "Stores contractor identities",
                "enabled": False,
                "id": "ACME-contractors",
                "links": {
                    "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                            "service_providers/ACME-contractors"
                },
                "relay_state_prefix": "ss:mem:",
                "sp_url": "https://other.example.com/identity/Shibboleth" +
                          ".sso/SAML2/ECP"
            }
        ]
    }

    def setUp(self):
        super(TestServiceProvidersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = service_providers_client.ServiceProvidersClient(
            fake_auth, 'identity', 'regionOne')

    def _test_register_service_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.register_service_provider,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_SERVICE_PROVIDER_INFO,
            bytes_body,
            service_provider_id="FAKE_ID",
            status=201)

    def _test_list_service_providers(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_service_providers,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SERVICE_PROVIDERS_INFO,
            bytes_body,
            status=200)

    def _test_get_service_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.get_service_provider,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SERVICE_PROVIDER_INFO,
            bytes_body,
            service_provider_id="FAKE_ID",
            status=200)

    def _test_delete_service_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.delete_service_provider,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            bytes_body,
            service_provider_id="FAKE_ID",
            status=204)

    def _test_update_service_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_service_provider,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_SERVICE_PROVIDER_INFO,
            bytes_body,
            service_provider_id="FAKE_ID",
            status=200)

    def test_register_service_provider_with_str_body(self):
        self._test_register_service_provider()

    def test_register_service_provider_with_bytes_body(self):
        self._test_register_service_provider(bytes_body=True)

    def test_list_service_providers_with_str_body(self):
        self._test_list_service_providers()

    def test_list_service_providers_with_bytes_body(self):
        self._test_list_service_providers(bytes_body=True)

    def test_get_service_provider_with_str_body(self):
        self._test_get_service_provider()

    def test_get_service_provider_with_bytes_body(self):
        self._test_get_service_provider(bytes_body=True)

    def test_delete_service_provider_with_str_body(self):
        self._test_delete_service_provider()

    def test_delete_service_provider_with_bytes_body(self):
        self._test_delete_service_provider(bytes_body=True)

    def test_update_service_provider_with_str_body(self):
        self._test_update_service_provider()

    def test_update_service_provider_with_bytes_body(self):
        self._test_update_service_provider(bytes_body=True)
