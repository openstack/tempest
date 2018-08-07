# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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

from tempest.lib.services.volume.v3 import extensions_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestExtensionsClient(base.BaseServiceTest):

    FAKE_EXTENSION_LIST = {
        "extensions": [
            {
                "updated": "2012-03-12T00:00:00+00:00",
                "name": "QuotaClasses",
                "links": [],
                "namespace": "fake-namespace-1",
                "alias": "os-quota-class-sets",
                "description": "Quota classes management support."
            },
            {
                "updated": "2013-05-29T00:00:00+00:00",
                "name": "VolumeTransfer",
                "links": [],
                "namespace": "fake-namespace-2",
                "alias": "os-volume-transfer",
                "description": "Volume transfer management support."
            },
            {
                "updated": "2014-02-10T00:00:00+00:00",
                "name": "VolumeManage",
                "links": [],
                "namespace": "fake-namespace-3",
                "alias": "os-volume-manage",
                "description": "Manage existing backend storage by Cinder."
            }
        ]
    }

    def setUp(self):
        super(TestExtensionsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = extensions_client.ExtensionsClient(fake_auth,
                                                         'volume',
                                                         'regionOne')

    def _test_list_extensions(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_extensions,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_EXTENSION_LIST,
            bytes_body)

    def test_list_extensions_with_str_body(self):
        self._test_list_extensions()

    def test_list_extensions_with_bytes_body(self):
        self._test_list_extensions(bytes_body=True)
