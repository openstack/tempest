# Copyright 2017 AT&T Corporation.
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

from tempest.lib.services.volume.v3 import capabilities_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestCapabilitiesClient(base.BaseServiceTest):

    FAKE_BACKEND_CAPABILITIES = {
        "namespace": "OS::Storage::Capabilities::fake",
        "vendor_name": "OpenStack",
        "volume_backend_name": "lvmdriver-1",
        "pool_name": "pool",
        "driver_version": "2.0.0",
        "storage_protocol": "iSCSI",
        "display_name": "Capabilities of Cinder LVM driver",
        "description": (
            "These are volume type options provided by Cinder LVM driver."),
        "visibility": "public",
        "replication_targets": [],
        "properties": {
            "compression": {
                "title": "Compression",
                "description": "Enables compression.",
                "type": "boolean"
            },
            "qos": {
                "title": "QoS",
                "description": "Enables QoS.",
                "type": "boolean"
            },
            "replication": {
                "title": "Replication",
                "description": "Enables replication.",
                "type": "boolean"
            },
            "thin_provisioning": {
                "title": "Thin Provisioning",
                "description": "Sets thin provisioning.",
                "type": "boolean"
            }
        }
    }

    def setUp(self):
        super(TestCapabilitiesClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = capabilities_client.CapabilitiesClient(
            fake_auth, 'volume', 'regionOne')

    def _test_show_backend_capabilities(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_backend_capabilities,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_BACKEND_CAPABILITIES,
            bytes_body,
            host='lvmdriver-1')

    def test_show_backend_capabilities_with_str_body(self):
        self._test_show_backend_capabilities()

    def test_show_backend_capabilities_with_bytes_body(self):
        self._test_show_backend_capabilities(bytes_body=True)
