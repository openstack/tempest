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

from tempest.lib.services.compute import networks_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestNetworksClient(base.BaseServiceTest):

    FAKE_NETWORK = {
        "bridge": None,
        "vpn_public_port": None,
        "dhcp_start": None,
        "bridge_interface": None,
        "share_address": None,
        "updated_at": None,
        "id": "34d5ae1e-5659-49cf-af80-73bccd7d7ad3",
        "cidr_v6": None,
        "deleted_at": None,
        "gateway": None,
        "rxtx_base": None,
        "label": u'30d7',
        "priority": None,
        "project_id": None,
        "vpn_private_address": None,
        "deleted": None,
        "vlan": None,
        "broadcast": None,
        "netmask": None,
        "injected": None,
        "cidr": None,
        "vpn_public_address": None,
        "multi_host": None,
        "enable_dhcp": None,
        "dns2": None,
        "created_at": None,
        "host": None,
        "mtu": None,
        "gateway_v6": None,
        "netmask_v6": None,
        "dhcp_server": None,
        "dns1": None
        }

    network_id = "34d5ae1e-5659-49cf-af80-73bccd7d7ad3"

    FAKE_NETWORKS = [FAKE_NETWORK]

    def setUp(self):
        super(TestNetworksClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = networks_client.NetworksClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_networks(self, bytes_body=False):
        fake_list = {"networks": self.FAKE_NETWORKS}
        self.check_service_client_function(
            self.client.list_networks,
            'tempest.lib.common.rest_client.RestClient.get',
            fake_list,
            bytes_body)

    def test_list_networks_with_str_body(self):
        self._test_list_networks()

    def test_list_networks_with_bytes_body(self):
        self._test_list_networks(bytes_body=True)

    def _test_show_network(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_network,
            'tempest.lib.common.rest_client.RestClient.get',
            {"network": self.FAKE_NETWORK},
            bytes_body,
            network_id=self.network_id
            )

    def test_show_network_with_str_body(self):
        self._test_show_network()

    def test_show_network_with_bytes_body(self):
        self._test_show_network(bytes_body=True)
