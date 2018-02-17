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
            "description": "fake application credential",
            "roles": [
                {
                    "id": "c60fdd45",
                    "domain_id": None,
                    "name": "Member"
                }
            ],
            "expires_at": "2019-02-27T18:30:59.999999Z",
            "secret": "_BVq0xU5L",
            "unrestricted": None,
            "project_id": "ddef321",
            "id": "5499a186",
            "name": "one"
        }
    }

    FAKE_LIST_APP_CREDS = {
        "application_credentials": [
            {
                "description": "fake application credential",
                "roles": [
                    {
                        "domain_id": None,
                        "name": "Member",
                        "id": "c60fdd45",
                    }
                ],
                "expires_at": "2018-02-27T18:30:59.999999Z",
                "unrestricted": None,
                "project_id": "ddef321",
                "id": "5499a186",
                "name": "one"
            },
            {
                "description": None,
                "roles": [
                    {
                        "id": "0f1837c8",
                        "domain_id": None,
                        "name": "anotherrole"
                    },
                    {
                        "id": "c60fdd45",
                        "domain_id": None,
                        "name": "Member"
                    }
                ],
                "expires_at": None,
                "unrestricted": None,
                "project_id": "c5403d938",
                "id": "d441c904f",
                "name": "two"
            }
        ]
    }

    FAKE_APP_CRED_INFO = {
        "application_credential": {
            "description": None,
            "roles": [
                {
                    "domain_id": None,
                    "name": "Member",
                    "id": "c60fdd45",
                }
            ],
            "expires_at": None,
            "unrestricted": None,
            "project_id": "ddef321",
            "id": "5499a186",
            "name": "one"
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
            application_credential_id="5499a186")

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

    def test_delete_trust(self):
        self.check_service_client_function(
            self.client.delete_application_credential,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            user_id="123456",
            application_credential_id="5499a186",
            status=204)
