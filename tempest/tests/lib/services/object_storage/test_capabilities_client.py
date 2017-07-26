# Copyright 2016 IBM Corp.
# All Rights Reserved.
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


from tempest.lib.services.object_storage import capabilities_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestCapabilitiesClient(base.BaseServiceTest):

    def setUp(self):
        super(TestCapabilitiesClient, self).setUp()
        self.fake_auth = fake_auth_provider.FakeAuthProvider()
        self.url = self.fake_auth.base_url(None)
        self.client = capabilities_client.CapabilitiesClient(
            self.fake_auth, 'swift', 'region1')

    def _test_list_capabilities(self, bytes_body=False):
        resp = {
            "swift": {
                "version": "1.11.0"
            },
            "slo": {
                "max_manifest_segments": 1000,
                "max_manifest_size": 2097152,
                "min_segment_size": 1
            },
            "staticweb": {},
            "tempurl": {}
        }
        self.check_service_client_function(
            self.client.list_capabilities,
            'tempest.lib.common.rest_client.RestClient.get',
            resp,
            bytes_body)

    def test_list_capabilities_with_str_body(self):
        self._test_list_capabilities()

    def test_list_capabilities_with_bytes_body(self):
        self._test_list_capabilities(True)
