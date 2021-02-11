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

from tempest.lib.services.identity.v3 import protocols_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestProtocolsClient(base.BaseServiceTest):
    FAKE_PROTOCOLS_INFO = {
        "links": {
            "next": None,
            "previous": None,
            "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                    "identity_providers/FAKE_ID/protocols"
        },
        "protocols": [
            {
                "id": "fake_id1",
                "links": {
                    "identity_provider": "http://example.com/identity/v3/" +
                                         "OS-FEDERATION/identity_providers/" +
                                         "FAKE_ID",
                    "self": "http://example.com/identity/v3/OS-FEDERATION/"
                            "identity_providers/FAKE_ID/protocols/fake_id1"
                },
                "mapping_id": "fake123"
            }
        ]
    }

    FAKE_PROTOCOL_INFO = {
        "protocol": {
            "id": "fake_id1",
            "links": {
                "identity_provider": "http://example.com/identity/v3/OS-" +
                                     "FEDERATION/identity_providers/FAKE_ID",
                "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                        "identity_providers/FAKE_ID/protocols/fake_id1"
            },
            "mapping_id": "fake123"
        }
    }

    def setUp(self):
        super(TestProtocolsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = protocols_client.ProtocolsClient(
            fake_auth, 'identity', 'regionOne')

    def _test_add_protocol_to_identity_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.add_protocol_to_identity_provider,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_PROTOCOL_INFO,
            bytes_body,
            idp_id="FAKE_ID",
            protocol_id="fake_id1",
            status=201)

    def _test_list_protocols_of_identity_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_protocols_of_identity_provider,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_PROTOCOLS_INFO,
            bytes_body,
            idp_id="FAKE_ID",
            status=200)

    def _test_get_protocol_for_identity_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.get_protocol_for_identity_provider,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_PROTOCOL_INFO,
            bytes_body,
            idp_id="FAKE_ID",
            protocol_id="fake_id1",
            status=200)

    def _test_update_mapping_for_identity_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_mapping_for_identity_provider,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_PROTOCOL_INFO,
            bytes_body,
            idp_id="FAKE_ID",
            protocol_id="fake_id1",
            status=200)

    def _test_delete_protocol_from_identity_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.delete_protocol_from_identity_provider,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            bytes_body,
            idp_id="FAKE_ID",
            protocol_id="fake_id1",
            status=204)

    def test_add_protocol_to_identity_provider_with_str_body(self):
        self._test_add_protocol_to_identity_provider()

    def test_add_protocol_to_identity_provider_with_bytes_body(self):
        self._test_add_protocol_to_identity_provider(bytes_body=True)

    def test_list_protocols_of_identity_provider_with_str_body(self):
        self._test_list_protocols_of_identity_provider()

    def test_list_protocols_of_identity_provider_with_bytes_body(self):
        self._test_list_protocols_of_identity_provider(bytes_body=True)

    def test_get_protocol_for_identity_provider_with_str_body(self):
        self._test_get_protocol_for_identity_provider()

    def test_get_protocol_for_identity_provider_with_bytes_body(self):
        self._test_get_protocol_for_identity_provider(bytes_body=True)

    def test_update_mapping_for_identity_provider_with_str_body(self):
        self._test_update_mapping_for_identity_provider()

    def test_update_mapping_for_identity_provider_with_bytes_body(self):
        self._test_update_mapping_for_identity_provider(bytes_body=True)

    def test_delete_protocol_from_identity_provider_with_str_body(self):
        self._test_delete_protocol_from_identity_provider()

    def test_delete_protocol_from_identity_provider_with_bytes_body(self):
        self._test_delete_protocol_from_identity_provider(bytes_body=False)
