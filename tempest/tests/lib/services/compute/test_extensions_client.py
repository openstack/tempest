# Copyright 2015 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.compute import extensions_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestExtensionsClient(base.BaseServiceTest):

    FAKE_SHOW_EXTENSION = {
        "extension": {
            "updated": "2011-06-09T00:00:00Z",
            "name": "Multinic",
            "links": [],
            "namespace":
            "http://docs.openstack.org/compute/ext/multinic/api/v1.1",
            "alias": "NMN",
            "description": u'\u2740(*\xb4\u25e1`*)\u2740'
        }
    }

    def setUp(self):
        super(TestExtensionsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = extensions_client.ExtensionsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_extensions(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_extensions,
            'tempest.lib.common.rest_client.RestClient.get',
            {"extensions": []},
            bytes_body)

    def test_list_extensions_with_str_body(self):
        self._test_list_extensions()

    def test_list_extensions_with_bytes_body(self):
        self._test_list_extensions(bytes_body=True)

    def _test_show_extension(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_extension,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SHOW_EXTENSION,
            bytes_body,
            extension_alias="NMN")

    def test_show_extension_with_str_body(self):
        self._test_show_extension()

    def test_show_extension_with_bytes_body(self):
        self._test_show_extension(bytes_body=True)
