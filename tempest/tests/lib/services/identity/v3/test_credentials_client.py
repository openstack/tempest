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

from tempest.lib.services.identity.v3 import credentials_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestCredentialsClient(base.BaseServiceTest):
    FAKE_CREATE_CREDENTIAL = {
        "credential": {
            "blob": "{\"access\":\"181920\",\"secret\":\"secretKey\"}",
            "project_id": "731fc6f265cd486d900f16e84c5cb594",
            "type": "ec2",
            "user_id": "bb5476fd12884539b41d5a88f838d773"
        }
    }

    FAKE_INFO_CREDENTIAL = {
        "credential": {
            "user_id": "bb5476fd12884539b41d5a88f838d773",
            "links": {
                "self": "http://example.com/identity/v3/credentials/" +
                        "207e9b76935efc03804d3dd6ab52d22e9b22a0711e4" +
                        "ada4ff8b76165a07311d7"
            },
            "blob": "{\"access\": \"a42a27755ce6442596b049bd7dd8a563\"," +
                    " \"secret\": \"71faf1d40bb24c82b479b1c6fbbd9f0c\"}",
            "project_id": "6e01855f345f4c59812999b5e459137d",
            "type": "ec2",
            "id": "207e9b76935efc03804d3dd6ab52d22e9b22a0711e4ada4f"
        }
    }

    FAKE_LIST_CREDENTIALS = {
        "credentials": [
            {
                "user_id": "bb5476fd12884539b41d5a88f838d773",
                "links": {
                    "self": "http://example.com/identity/v3/credentials/" +
                            "207e9b76935efc03804d3dd6ab52d22e9b22a0711e4" +
                            "ada4ff8b76165a07311d7"
                },
                "blob": "{\"access\": \"a42a27755ce6442596b049bd7dd8a563\"," +
                        " \"secret\": \"71faf1d40bb24c82b479b1c6fbbd9f0c\"," +
                        " \"trust_id\": null}",
                "project_id": "6e01855f345f4c59812999b5e459137d",
                "type": "ec2",
                "id": "207e9b76935efc03804d3dd6ab52d22e9b22a0711e4ada4f"
            },
            {
                "user_id": "6f556708d04b4ea6bc72d7df2296b71a",
                "links": {
                    "self": "http://example.com/identity/v3/credentials/" +
                            "2441494e52ab6d594a34d74586075cb299489bdd1e9" +
                            "389e3ab06467a4f460609"
                },
                "blob": "{\"access\": \"7da79ff0aa364e1396f067e352b9b79a\"," +
                        " \"secret\": \"7a18d68ba8834b799d396f3ff6f1e98c\"," +
                        " \"trust_id\": null}",
                "project_id": "1a1d14690f3c4ec5bf5f321c5fde3c16",
                "type": "ec2",
                "id": "2441494e52ab6d594a34d74586075cb299489bdd1e9389e3"
            },
            {
                "user_id": "c14107e65d5c4a7f8894fc4b3fc209ff",
                "links": {
                    "self": "http://example.com/identity/v3/credentials/" +
                            "3397b204b5f04c495bcdc8f34c8a39996f280f91726" +
                            "58241873e15f070ec79d7"
                },
                "blob": "{\"access\": \"db9c58a558534a10a070110de4f9f20c\"," +
                        " \"secret\": \"973e790b88db447ba6f93bca02bc745b\"," +
                        " \"trust_id\": null}",
                "project_id": "7396e43183db40dcbf40dd727637b548",
                "type": "ec2",
                "id": "3397b204b5f04c495bcdc8f34c8a39996f280f9172658241"
            },
            {
                "user_id": "bb5476fd12884539b41d5a88f838d773",
                "links": {
                    "self": "http://example.com/identity/v3/credentials/" +
                            "7ef4faa904ae7b8b4ddc7bad15b05ee359dad7d7a9b" +
                            "82861d4ad92fdbbb2eb4e"
                },
                "blob": "{\"access\": \"7d7559359b57419eb5f5f5dcd65ab57d\"," +
                        " \"secret\": \"570652bcf8c2483c86eb29e9734eed3c\"," +
                        " \"trust_id\": null}",
                "project_id": "731fc6f265cd486d900f16e84c5cb594",
                "type": "ec2",
                "id": "7ef4faa904ae7b8b4ddc7bad15b05ee359dad7d7a9b82861"
            },
        ],
        "links": {
            "self": "http://example.com/identity/v3/credentials",
            "previous": None,
            "next": None
        }
    }

    def setUp(self):
        super(TestCredentialsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = credentials_client.CredentialsClient(fake_auth,
                                                           'identity',
                                                           'regionOne')

    def _test_create_credential(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_credential,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_CREDENTIAL,
            bytes_body, status=201)

    def _test_show_credential(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_credential,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_INFO_CREDENTIAL,
            bytes_body,
            credential_id="207e9b76935efc03804d3dd6ab52d22e9b22a0711e4ada4f")

    def _test_update_credential(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_credential,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_INFO_CREDENTIAL,
            bytes_body,
            credential_id="207e9b76935efc03804d3dd6ab52d22e9b22a0711e4ada4f")

    def _test_list_credentials(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_credentials,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_CREDENTIALS,
            bytes_body)

    def test_create_credential_with_str_body(self):
        self._test_create_credential()

    def test_create_credential_with_bytes_body(self):
        self._test_create_credential(bytes_body=True)

    def test_show_credential_with_str_body(self):
        self._test_show_credential()

    def test_show_credential_with_bytes_body(self):
        self._test_show_credential(bytes_body=True)

    def test_update_credential_with_str_body(self):
        self._test_update_credential()

    def test_update_credential_with_bytes_body(self):
        self._test_update_credential(bytes_body=True)

    def test_list_credentials_with_str_body(self):
        self._test_list_credentials()

    def test_list_credentials_with_bytes_body(self):
        self._test_list_credentials(bytes_body=True)

    def test_delete_credential(self):
        self.check_service_client_function(
            self.client.delete_credential,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            credential_id="207e9b76935efc03804d3dd6ab52d22e9b22a0711e4ada4f",
            status=204)
