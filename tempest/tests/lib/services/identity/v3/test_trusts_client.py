# Copyright 2016 Red Hat, Inc.
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

from tempest.lib.services.identity.v3 import trusts_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestTrustsClient(base.BaseServiceTest):
    FAKE_CREATE_TRUST = {
        "trust": {
            "expires_at": "2013-02-27T18:30:59.999999Z",
            "impersonation": True,
            "allow_redelegation": True,
            "project_id": "ddef321",
            "roles": [
                {
                    "name": "member"
                    }
                ],
            "trustee_user_id": "86c0d5",
            "trustor_user_id": "a0fdfd"
            }
        }

    FAKE_LIST_TRUSTS = {
        "trusts": [
            {
                "id": "1ff900",
                "expires_at":
                "2013-02-27T18:30:59.999999Z",
                "impersonation": True,
                "links": {
                    "self":
                    "http://example.com/identity/v3/OS-TRUST/trusts/1ff900"
                    },
                "project_id": "0f1233",
                "trustee_user_id": "86c0d5",
                "trustor_user_id": "a0fdfd"
                },
            {
                "id": "f4513a",
                "impersonation": False,
                "links": {
                    "self":
                    "http://example.com/identity/v3/OS-TRUST/trusts/f45513a"
                    },
                "project_id": "0f1233",
                "trustee_user_id": "86c0d5",
                "trustor_user_id": "3cd2ce"
                }
            ]
        }

    FAKE_TRUST_INFO = {
        "trust": {
            "id": "987fe8",
            "expires_at": "2013-02-27T18:30:59.999999Z",
            "impersonation": True,
            "links": {
                "self":
                "http://example.com/identity/v3/OS-TRUST/trusts/987fe8"
                },
            "roles": [
                {
                    "id": "ed7b78",
                    "links": {
                        "self":
                        "http://example.com/identity/v3/roles/ed7b78"
                        },
                    "name": "member"
                    }
                ],
            "roles_links": {
                "next": None,
                "previous": None,
                "self":
                "http://example.com/identity/v3/OS-TRUST/trusts/1ff900/roles"
                },
            "project_id": "0f1233",
            "trustee_user_id": "be34d1",
            "trustor_user_id": "56ae32"
            }
        }

    def setUp(self):
        super(TestTrustsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = trusts_client.TrustsClient(fake_auth, 'identity',
                                                 'regionOne')

    def _test_create_trust(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_trust,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_TRUST,
            bytes_body,
            status=201)

    def _test_show_trust(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_trust,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_TRUST_INFO,
            bytes_body,
            trust_id="1ff900")

    def _test_list_trusts(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_trusts,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_TRUSTS,
            bytes_body)

    def test_create_trust_with_str_body(self):
        self._test_create_trust()

    def test_create_trust_with_bytes_body(self):
        self._test_create_trust(bytes_body=True)

    def test_show_trust_with_str_body(self):
        self._test_show_trust()

    def test_show_trust_with_bytes_body(self):
        self._test_show_trust(bytes_body=True)

    def test_list_trusts_with_str_body(self):
        self._test_list_trusts()

    def test_list_trusts_with_bytes_body(self):
        self._test_list_trusts(bytes_body=True)

    def test_delete_trust(self):
        self.check_service_client_function(
            self.client.delete_trust,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            trust_id="1ff900",
            status=204)
