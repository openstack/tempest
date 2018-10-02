# Copyright 2016 VMware, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.lib.services.network import versions_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestNetworkVersionsClient(base.BaseServiceTest):
    VERSION = "v2.0"

    FAKE_VERSIONS_INFO = {
        "versions": [
            {
                "id": "v2.0",
                "links": [
                    {
                        "href": "http://openstack.example.com/%s/" % VERSION,
                        "rel": "self"
                    }
                ],
                "status": "CURRENT"
            }
        ]
    }

    FAKE_VERSION_DETAILS = {
        "resources": [
            {
                "collection": "subnets",
                "links": [
                    {
                        "href": "http://openstack.example.com:9696/"
                                "%s/subnets" % VERSION,
                        "rel": "self"
                    }
                ],
                "name": "subnet"
            },
            {
                "collection": "networks",
                "links": [
                    {
                        "href": "http://openstack.example.com:9696/"
                                "%s/networks" % VERSION,
                        "rel": "self"
                    }
                ],
                "name": "network"
            },
            {
                "collection": "ports",
                "links": [
                    {
                        "href": "http://openstack.example.com:9696/"
                                "%s/ports" % VERSION,
                        "rel": "self"
                    }
                ],
                "name": "port"
            }
        ]
    }

    def setUp(self):
        super(TestNetworkVersionsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.versions_client = versions_client.NetworkVersionsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_versions_client(self, func, body, bytes_body=False, **kwargs):
        self.check_service_client_function(
            func, 'tempest.lib.common.rest_client.RestClient.raw_request',
            body, bytes_body, 200, **kwargs)

    def test_list_versions_client_with_str_body(self):
        self._test_versions_client(self.versions_client.list_versions,
                                   self.FAKE_VERSIONS_INFO)

    def test_list_versions_client_with_bytes_body(self):
        self._test_versions_client(self.versions_client.list_versions,
                                   self.FAKE_VERSIONS_INFO, bytes_body=True)

    def test_show_version_client_with_str_body(self):
        self._test_versions_client(self.versions_client.show_version,
                                   self.FAKE_VERSION_DETAILS,
                                   version=self.VERSION)

    def test_show_version_client_with_bytes_body(self):
        self._test_versions_client(self.versions_client.show_version,
                                   self.FAKE_VERSION_DETAILS, bytes_body=True,
                                   version=self.VERSION)
