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

from tempest.lib.services.volume.v2 import encryption_types_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestEncryptionTypesClient(base.BaseServiceTest):
    FAKE_CREATE_ENCRYPTION_TYPE = {
        "encryption": {
            "id": "cbc36478b0bd8e67e89",
            "name": "FakeEncryptionType",
            "type": "fakeType",
            "provider": "LuksEncryptor",
            "cipher": "aes-xts-plain64",
            "key_size": "512",
            "control_location": "front-end"
        }
    }

    FAKE_INFO_ENCRYPTION_TYPE = {
        "encryption": {
            "name": "FakeEncryptionType",
            "type": "fakeType",
            "description": "test_description",
            "volume_type": "fakeType",
            "provider": "LuksEncryptor",
            "cipher": "aes-xts-plain64",
            "key_size": "512",
            "control_location": "front-end"
        }
    }

    FAKE_ENCRYPTION_SPECS_ITEM = {
        "cipher": "aes-xts-plain64"
    }

    def setUp(self):
        super(TestEncryptionTypesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = encryption_types_client.EncryptionTypesClient(fake_auth,
                                                                    'volume',
                                                                    'regionOne'
                                                                    )

    def _test_create_encryption(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_encryption_type,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_ENCRYPTION_TYPE,
            bytes_body, volume_type_id="cbc36478b0bd8e67e89")

    def _test_show_encryption_type(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_encryption_type,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_INFO_ENCRYPTION_TYPE,
            bytes_body, volume_type_id="cbc36478b0bd8e67e89")

    def _test_show_encryption_specs_item(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_encryption_specs_item,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ENCRYPTION_SPECS_ITEM,
            bytes_body, volume_type_id="cbc36478b0bd8e67e89", key="cipher")

    def test_create_encryption_type_with_str_body(self):
        self._test_create_encryption()

    def test_create_encryption_type_with_bytes_body(self):
        self._test_create_encryption(bytes_body=True)

    def test_show_encryption_type_with_str_body(self):
        self._test_show_encryption_type()

    def test_show_encryption_type_with_bytes_body(self):
        self._test_show_encryption_type(bytes_body=True)

    def test_show_encryption_specs_item_with_str_body(self):
        self._test_show_encryption_specs_item()

    def test_show_encryption_specs_item_with_bytes_body(self):
        self._test_show_encryption_specs_item(bytes_body=True)

    def test_delete_encryption_type(self):
        self.check_service_client_function(
            self.client.delete_encryption_type,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            volume_type_id="cbc36478b0bd8e67e89",
            status=202)
