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

from tempest.lib.services.identity.v3 import identity_providers_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestIdentityProvidersClient(base.BaseServiceTest):
    FAKE_IDENTITY_PROVIDERS_INFO = {
        "identity_providers": [
            {
                "domain_id": "FAKE_DOMAIN_ID",
                "description": "FAKE IDENTITY PROVIDER",
                "remote_ids": ["fake_id_1", "fake_id_2"],
                "enabled": True,
                "id": "FAKE_ID",
                "links": {
                    "protocols": "http://example.com/identity/v3/" +
                                 "OS-FEDERATION/identity_providers/" +
                                 "FAKE_ID/protocols",
                    "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                            "identity_providers/FAKE_ID"
                }
            }
        ],
        "links": {
            "next": None,
            "previous": None,
            "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                    "identity_providers"
        }
    }

    FAKE_IDENTITY_PROVIDER_INFO = {
        "identity_provider": {
            "authorization_ttl": None,
            "domain_id": "FAKE_DOMAIN_ID",
            "description": "FAKE IDENTITY PROVIDER",
            "remote_ids": ["fake_id_1", "fake_id_2"],
            "enabled": True,
            "id": "ACME",
            "links": {
                "protocols": "http://example.com/identity/v3/OS-FEDERATION/" +
                             "identity_providers/FAKE_ID/protocols",
                "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                        "identity_providers/FAKE_ID"
            }
        }
    }

    def setUp(self):
        super(TestIdentityProvidersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = identity_providers_client.IdentityProvidersClient(
            fake_auth, 'identity', 'regionOne')

    def _test_register_identity_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.register_identity_provider,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_IDENTITY_PROVIDER_INFO,
            bytes_body,
            identity_provider_id="FAKE_ID",
            status=201)

    def _test_list_identity_providers(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_identity_providers,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_IDENTITY_PROVIDERS_INFO,
            bytes_body,
            status=200)

    def _test_get_identity_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.get_identity_provider,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_IDENTITY_PROVIDER_INFO,
            bytes_body,
            identity_provider_id="FAKE_ID",
            status=200)

    def _test_delete_identity_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.delete_identity_provider,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            bytes_body,
            identity_provider_id="FAKE_ID",
            status=204)

    def _test_update_identity_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_identity_provider,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_IDENTITY_PROVIDER_INFO,
            bytes_body,
            identity_provider_id="FAKE_ID",
            status=200)

    def test_register_identity_provider_with_str_body(self):
        self._test_register_identity_provider()

    def test_register_identity_provider_with_bytes_body(self):
        self._test_register_identity_provider(bytes_body=True)

    def test_list_identity_providers_with_str_body(self):
        self._test_list_identity_providers()

    def test_list_identity_providers_with_bytes_body(self):
        self._test_list_identity_providers(bytes_body=True)

    def test_get_identity_provider_with_str_body(self):
        self._test_get_identity_provider()

    def test_get_identity_provider_with_bytes_body(self):
        self._test_get_identity_provider(bytes_body=True)

    def test_delete_identity_provider_with_str_body(self):
        self._test_delete_identity_provider()

    def test_delete_identity_provider_with_bytes_body(self):
        self._test_delete_identity_provider(bytes_body=True)

    def test_update_identity_provider_with_str_body(self):
        self._test_update_identity_provider()

    def test_update_identity_provider_with_bytes_body(self):
        self._test_update_identity_provider(bytes_body=True)
