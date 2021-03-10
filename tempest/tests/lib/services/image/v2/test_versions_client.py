# Copyright 2017 NEC Corporation.  All rights reserved.
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

import fixtures

from tempest.lib.services.image.v2 import versions_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestVersionsClient(base.BaseServiceTest):

    FAKE_VERSIONS_INFO = {
        "versions": [
            {
                "status": "CURRENT", "id": "v2.5",
                "links": [
                    {"href": "https://10.220.1.21:9292/v2/", "rel": "self"}
                ]
            },
            {
                "status": "SUPPORTED", "id": "v2.4",
                "links": [
                    {"href": "https://10.220.1.21:9292/v2/", "rel": "self"}
                ]
            },
            {
                "status": "SUPPORTED", "id": "v2.3",
                "links": [
                    {"href": "https://10.220.1.21:9292/v2/", "rel": "self"}
                ]
            },
            {
                "status": "SUPPORTED", "id": "v2.2",
                "links": [
                    {"href": "https://10.220.1.21:9292/v2/", "rel": "self"}
                ]
            },
            {
                "status": "SUPPORTED", "id": "v2.1",
                "links": [
                    {"href": "https://10.220.1.21:9292/v2/", "rel": "self"}
                ]
            },
            {
                "status": "SUPPORTED", "id": "v2.0",
                "links": [
                    {"href": "https://10.220.1.21:9292/v2/", "rel": "self"}
                ]
            },
            {
                "status": "DEPRECATED", "id": "v1.1",
                "links": [
                    {"href": "https://10.220.1.21:9292/v1/", "rel": "self"}
                ]
            },
            {
                "status": "DEPRECATED", "id": "v1.0",
                "links": [
                    {"href": "https://10.220.1.21:9292/v1/", "rel": "self"}
                ]
            }
        ]
    }

    def setUp(self):
        super(TestVersionsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = versions_client.VersionsClient(fake_auth,
                                                     'image',
                                                     'regionOne')

    def _test_list_versions(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_versions,
            'tempest.lib.common.rest_client.RestClient.raw_request',
            self.FAKE_VERSIONS_INFO,
            bytes_body,
            300)

    def test_list_versions_with_str_body(self):
        self._test_list_versions()

    def test_list_versions_with_bytes_body(self):
        self._test_list_versions(bytes_body=True)

    def test_has_version(self):
        mocked_r = self.create_response(self.FAKE_VERSIONS_INFO, False,
                                        300, None)
        self.useFixture(fixtures.MockPatch(
            'tempest.lib.common.rest_client.RestClient.raw_request',
            return_value=mocked_r))

        self.assertTrue(self.client.has_version('2.1'))
        self.assertFalse(self.client.has_version('9.9'))
