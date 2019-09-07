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

from tempest.lib.services.volume.v3 import versions_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestVersionsClient(base.BaseServiceTest):

    FAKE_VERSIONS_INFO = {
        "versions": [
            {
                "status": "DEPRECATED", "updated": "2016-05-02T20:25:19Z",
                "links": [
                    {"href": "http://docs.openstack.org/", "type": "text/html",
                     "rel": "describedby"},
                    {"href": "https://10.30.197.39:8776/v1/", "rel": "self"}
                ],
                "min_version": "",
                "version": "",
                "media-types": [
                    {"base": "application/json",
                     "type": "application/vnd.openstack.volume+json;version=1"}
                ],
                "id": "v1.0"
            },
            {
                "status": "DEPRECATED", "updated": "2017-02-25T12:00:00Z",
                "links": [
                    {"href": "http://docs.openstack.org/", "type": "text/html",
                     "rel": "describedby"},
                    {"href": "https://10.30.197.39:8776/v2/", "rel": "self"}
                ],
                "min_version": "",
                "version": "",
                "media-types": [
                    {"base": "application/json",
                     "type": "application/vnd.openstack.volume+json;version=1"}
                ],
                "id": "v2.0"
            },
            {
                "status": "CURRENT", "updated": "2016-02-08T12:20:21Z",
                "links": [
                    {"href": "http://docs.openstack.org/", "type": "text/html",
                     "rel": "describedby"},
                    {"href": "https://10.30.197.39:8776/v3/", "rel": "self"}
                ],
                "min_version": "3.0",
                "version": "3.28",
                "media-types": [
                    {"base": "application/json",
                     "type": "application/vnd.openstack.volume+json;version=1"}
                ],
                "id": "v3.0"
            }
        ]
    }

    FAKE_VERSION_DETAILS = {
        "versions": [
            {
                "id": "v3.0",
                "links": [
                    {"href": "https://docs.openstack.org/",
                     "type": "text/html", "rel": "describedby"},
                    {"href": "http://127.0.0.1:44895/v3/", "rel": "self"}
                ],
                "media-types": [
                    {"base": "application/json",
                     "type": "application/vnd.openstack.volume+json;version=3"}
                ],
                "min_version": "3.0",
                "status": "CURRENT",
                "updated": "2018-07-17T00:00:00Z",
                "version": "3.59"
            }
        ]
    }

    def setUp(self):
        super(TestVersionsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = versions_client.VersionsClient(fake_auth,
                                                     'volume',
                                                     'regionOne')

    def _test_get_base_version_url(self, url, expected_base_url):
        fake_auth = fake_auth_provider.FakeAuthProvider(fake_base_url=url)
        client = versions_client.VersionsClient(fake_auth,
                                                'volume',
                                                'regionOne')
        self.assertEqual(expected_base_url,
                         client._get_base_version_url())

    def _test_list_versions(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_versions,
            'tempest.lib.common.rest_client.RestClient.raw_request',
            self.FAKE_VERSIONS_INFO,
            bytes_body,
            300)

    def _test_show_version(self, version, bytes_body=False):
        self.check_service_client_function(
            self.client.show_version,
            'tempest.lib.common.rest_client.RestClient.raw_request',
            self.FAKE_VERSION_DETAILS,
            bytes_body,
            200, version=version)

    def test_list_versions_with_str_body(self):
        self._test_list_versions()

    def test_list_versions_with_bytes_body(self):
        self._test_list_versions(bytes_body=True)

    def test_show_version_details_with_str_body(self):
        self._test_show_version('v3')

    def test_show_version_details_with_bytes_body(self):
        self._test_show_version('v3', bytes_body=True)

    def test_get_base_version_url_app_name(self):
        self._test_get_base_version_url('https://bar.org/volume/v1/123',
                                        'https://bar.org/volume/')
        self._test_get_base_version_url('https://bar.org/volume/v2/123',
                                        'https://bar.org/volume/')
        self._test_get_base_version_url('https://bar.org/volume/v3/123',
                                        'https://bar.org/volume/')
