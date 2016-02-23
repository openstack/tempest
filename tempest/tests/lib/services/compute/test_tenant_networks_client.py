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

from tempest.lib.services.compute import tenant_networks_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services.compute import base


class TestTenantNetworksClient(base.BaseComputeServiceTest):

    FAKE_NETWORK = {
        "cidr": "None",
        "id": "c2329eb4-cc8e-4439-ac4c-932369309e36",
        "label": u'\u30d7'
        }

    FAKE_NETWORKS = [FAKE_NETWORK]

    NETWORK_ID = FAKE_NETWORK['id']

    def setUp(self):
        super(TestTenantNetworksClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = tenant_networks_client.TenantNetworksClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_tenant_networks(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_tenant_networks,
            'tempest.lib.common.rest_client.RestClient.get',
            {"networks": self.FAKE_NETWORKS},
            bytes_body)

    def test_list_tenant_networks_with_str_body(self):
        self._test_list_tenant_networks()

    def test_list_tenant_networks_with_bytes_body(self):
        self._test_list_tenant_networks(bytes_body=True)

    def _test_show_tenant_network(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_tenant_network,
            'tempest.lib.common.rest_client.RestClient.get',
            {"network": self.FAKE_NETWORK},
            bytes_body,
            network_id=self.NETWORK_ID)

    def test_show_tenant_network_with_str_body(self):
        self._test_show_tenant_network()

    def test_show_tenant_network_with_bytes_body(self):
        self._test_show_tenant_network(bytes_body=True)
