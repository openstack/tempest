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

import httplib2

from oslo_serialization import jsonutils as json
from oslotest import mockpatch

from tempest.services.compute.json import tenant_networks_client
from tempest.tests import base
from tempest.tests import fake_auth_provider


class TestTenantNetworksClient(base.TestCase):

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
        serialized_body = json.dumps({"networks": self.FAKE_NETWORKS})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.list_tenant_networks()
        self.assertEqual({"networks": self.FAKE_NETWORKS}, resp)

    def test_list_tenant_networks_with_str_body(self):
        self._test_list_tenant_networks()

    def test_list_tenant_networks_with_bytes_body(self):
        self._test_list_tenant_networks(bytes_body=True)

    def _test_show_tenant_network(self, bytes_body=False):
        serialized_body = json.dumps({"network": self.FAKE_NETWORK})
        if bytes_body:
            serialized_body = serialized_body.encode('utf-8')

        mocked_resp = (httplib2.Response({'status': 200}), serialized_body)
        self.useFixture(mockpatch.Patch(
            'tempest.common.service_client.ServiceClient.get',
            return_value=mocked_resp))
        resp = self.client.show_tenant_network(self.NETWORK_ID)
        self.assertEqual({"network": self.FAKE_NETWORK}, resp)

    def test_show_tenant_network_with_str_body(self):
        self._test_show_tenant_network()

    def test_show_tenant_network_with_bytes_body(self):
        self._test_show_tenant_network(bytes_body=True)
