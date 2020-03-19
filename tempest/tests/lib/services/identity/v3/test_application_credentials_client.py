# Copyright 2018 SUSE Linux GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.lib.services.identity.v3 import application_credentials_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestApplicationCredentialsClient(base.BaseServiceTest):
    FAKE_CREATE_APP_CRED = {
        "application_credential": {
            "name": "monitoring",
            "secret": "rEaqvJka48mpv",
            "description": "Application credential for monitoring.",
            "expires_at": "2018-02-27T18:30:59Z",
            "roles": [
                {"name": "Reader"}
            ],
            "access_rules": [
                {
                    "path": "/v2.0/metrics",
                    "method": "GET",
                    "service": "monitoring"
                }
            ],
            "unrestricted": False
        }
    }

    FAKE_LIST_APP_CREDS = {
        "links": {
            "self": "http://example.com/identity/v3/users/" +
                    "fd786d56402c4d1691372e7dee0d00b5/application_credentials",
            "previous": None,
            "next": None
        },
        "application_credentials": [
            {
                "description": "Application credential for backups.",
                "roles": [
                    {
                        "domain_id": None,
                        "name": "Writer",
                        "id": "6aff702516544aeca22817fd3bc39683"
                    }
                ],
                "access_rules": [
                ],
                "links": {
                    "self": "http://example.com/identity/v3/users/" +
                            "fd786d56402c4d1691372e7dee0d00b5/" +
                            "application_credentials/" +
                            "308a7e905eee4071aac5971744c061f6"
                },
                "expires_at": "2018-02-27T18:30:59.000000",
                "unrestricted": False,
                "project_id": "231c62fb0fbd485b995e8b060c3f0d98",
                "id": "308a7e905eee4071aac5971744c061f6",
                "name": "backups"
            },
            {
                "description": "Application credential for monitoring.",
                "roles": [
                    {
                        "id": "6aff702516544aeca22817fd3bc39683",
                        "domain_id": None,
                        "name": "Reader"
                    }
                ],
                "access_rules": [
                    {
                        "path": "/v2.0/metrics",
                        "id": "07d719df00f349ef8de77d542edf010c",
                        "service": "monitoring",
                        "method": "GET"
                    }
                ],
                "links": {
                    "self": "http://example.com/identity/v3/users/" +
                            "fd786d56402c4d1691372e7dee0d00b5/" +
                            "application_credentials/" +
                            "58d61ff8e6e34accb35874016d1dba8b"
                },
                "expires_at": "2018-02-27T18:30:59.000000",
                "unrestricted": False,
                "project_id": "231c62fb0fbd485b995e8b060c3f0d98",
                "id": "58d61ff8e6e34accb35874016d1dba8b",
                "name": "monitoring"
            }
        ]
    }

    FAKE_APP_CRED_INFO = {
        "application_credential": {
            "description": "Application credential for monitoring.",
            "roles": [
                {
                    "id": "6aff702516544aeca22817fd3bc39683",
                    "domain_id": None,
                    "name": "Reader"
                }
            ],
            "access_rules": [
                {
                    "path": "/v2.0/metrics",
                    "id": "07d719df00f349ef8de77d542edf010c",
                    "service": "monitoring",
                    "method": "GET"
                }
            ],
            "links": {
                "self": "http://example.com/identity/v3/users/" +
                        "fd786d56402c4d1691372e7dee0d00b5/" +
                        "application_credentials/" +
                        "58d61ff8e6e34accb35874016d1dba8b"
            },
            "expires_at": "2018-02-27T18:30:59.000000",
            "unrestricted": False,
            "project_id": "231c62fb0fbd485b995e8b060c3f0d98",
            "id": "58d61ff8e6e34accb35874016d1dba8b",
            "name": "monitoring"
        }
    }

    def setUp(self):
        super(TestApplicationCredentialsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = \
            application_credentials_client.ApplicationCredentialsClient(
                fake_auth, 'identity', 'regionOne')

    def _test_create_app_cred(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_application_credential,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_APP_CRED,
            bytes_body,
            status=201,
            user_id="123456")

    def _test_show_app_cred(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_application_credential,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_APP_CRED_INFO,
            bytes_body,
            user_id="123456",
            application_credential_id="58d61ff8e6e34accb35874016d1dba8b")

    def _test_list_app_creds(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_application_credentials,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_APP_CREDS,
            bytes_body,
            user_id="123456")

    def test_create_application_credential_with_str_body(self):
        self._test_create_app_cred()

    def test_create_application_credential_with_bytes_body(self):
        self._test_create_app_cred(bytes_body=True)

    def test_show_application_credential_with_str_body(self):
        self._test_show_app_cred()

    def test_show_application_credential_with_bytes_body(self):
        self._test_show_app_cred(bytes_body=True)

    def test_list_application_credential_with_str_body(self):
        self._test_list_app_creds()

    def test_list_application_credential_with_bytes_body(self):
        self._test_list_app_creds(bytes_body=True)

    def test_delete_application_credential(self):
        self.check_service_client_function(
            self.client.delete_application_credential,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            user_id="123456",
            application_credential_id="58d61ff8e6e34accb35874016d1dba8b",
            status=204)
