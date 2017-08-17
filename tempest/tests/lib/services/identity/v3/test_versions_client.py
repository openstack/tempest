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

from tempest.lib.services.identity.v3 import versions_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestIdentityClient(base.BaseServiceTest):

    FAKE_VERSIONS_INFO = {
        "versions": {
            "values": [
                {"status": "stable", "updated": "2017-02-22T00:00:00Z",
                 "media-types": [
                     {"base": "application/json", "type":
                      "application/vnd.openstack.identity-v3+json"}
                 ],
                 "id": "v3.8",
                 "links": [
                     {"href": "https://15.184.67.226/identity_admin/v3/",
                      "rel": "self"}
                 ]},
                {"status": "deprecated", "updated": "2016-08-04T00:00:00Z",
                 "media-types": [
                     {"base": "application/json",
                      "type": "application/vnd.openstack.identity-v2.0+json"}
                 ],
                 "id": "v2.0",
                 "links": [
                     {"href": "https://15.184.67.226/identity_admin/v2.0/",
                      "rel": "self"},
                     {"href": "https://docs.openstack.org/",
                      "type": "text/html", "rel": "describedby"}
                 ]}
            ]
        }
    }

    def setUp(self):
        super(TestIdentityClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = versions_client.VersionsClient(fake_auth,
                                                     'identity',
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
