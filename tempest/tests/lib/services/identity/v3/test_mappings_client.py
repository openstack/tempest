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

from tempest.lib.services.identity.v3 import mappings_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestMappingsClient(base.BaseServiceTest):
    FAKE_MAPPING_INFO = {
        "mapping": {
            "id": "fake123",
            "links": {
                "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                        "mappings/fake123"
            },
            "rules": [
                {
                    "local": [
                        {
                            "user": {
                                "name": "{0}"
                            }
                        },
                        {
                            "group": {
                                "id": "0cd5e9"
                            }
                        }
                    ],
                    "remote": [
                        {
                            "type": "UserName"
                        },
                        {
                            "type": "orgPersonType",
                            "not_any_of": [
                                "Contractor",
                                "Guest"
                            ]
                        }
                    ]
                }
            ]
        }
    }

    FAKE_MAPPINGS_INFO = {
        "links": {
            "next": None,
            "previous": None,
            "self": "http://example.com/identity/v3/OS-FEDERATION/mappings"
        },
        "mappings": [
            {
                "id": "fake123",
                "links": {
                    "self": "http://example.com/identity/v3/OS-FEDERATION/" +
                            "mappings/fake123"
                },
                "rules": [
                    {
                        "local": [
                            {
                                "user": {
                                    "name": "{0}"
                                }
                            },
                            {
                                "group": {
                                    "id": "0cd5e9"
                                }
                            }
                        ],
                        "remote": [
                            {
                                "type": "UserName"
                            },
                            {
                                "type": "orgPersonType",
                                "any_one_of": [
                                    "Contractor",
                                    "SubContractor"
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }

    def setUp(self):
        super(TestMappingsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = mappings_client.MappingsClient(
            fake_auth, 'identity', 'regionOne')

    def _test_create_mapping(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_mapping,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_MAPPING_INFO,
            bytes_body,
            mapping_id="fake123",
            status=201)

    def _test_get_mapping(self, bytes_body=False):
        self.check_service_client_function(
            self.client.get_mapping,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_MAPPING_INFO,
            bytes_body,
            mapping_id="fake123",
            status=200)

    def _test_update_mapping(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_mapping,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_MAPPING_INFO,
            bytes_body,
            mapping_id="fake123",
            status=200)

    def _test_list_mappings(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_mappings,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_MAPPINGS_INFO,
            bytes_body,
            status=200)

    def _test_delete_mapping(self, bytes_body=False):
        self.check_service_client_function(
            self.client.delete_mapping,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            bytes_body,
            mapping_id="fake123",
            status=204)

    def test_create_mapping_with_str_body(self):
        self._test_create_mapping()

    def test_create_mapping_with_bytes_body(self):
        self._test_create_mapping(bytes_body=True)

    def test_get_mapping_with_str_body(self):
        self._test_get_mapping()

    def test_get_mapping_with_bytes_body(self):
        self._test_get_mapping(bytes_body=True)

    def test_update_mapping_with_str_body(self):
        self._test_update_mapping()

    def test_update_mapping_with_bytes_body(self):
        self._test_update_mapping(bytes_body=True)

    def test_list_mappings_with_str_body(self):
        self._test_list_mappings()

    def test_list_mappings_with_bytes_body(self):
        self._test_list_mappings(bytes_body=True)

    def test_delete_mapping_with_str_body(self):
        self._test_delete_mapping()

    def test_delete_mapping_with_bytes_body(self):
        self._test_delete_mapping(bytes_body=True)
