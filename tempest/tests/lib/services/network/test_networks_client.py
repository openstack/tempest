# Copyright 2017 AT&T Corporation.
# All rights reserved.
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

import copy

from tempest.lib.services.network import networks_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestNetworksClient(base.BaseServiceTest):

    FAKE_NETWORKS = {
        "networks": [
            {
                "admin_state_up": True,
                "availability_zone_hints": [],
                "availability_zones": [
                    "nova"
                ],
                "created_at": "2016-03-08T20:19:41",
                "dns_domain": "my-domain.org.",
                "id": "d32019d3-bc6e-4319-9c1d-6722fc136a22",
                "ipv4_address_scope": None,
                "ipv6_address_scope": None,
                "l2_adjacency": False,
                "mtu": 0,
                "name": "net1",
                "port_security_enabled": True,
                "project_id": "4fd44f30292945e481c7b8a0c8908869",
                "qos_policy_id": "6a8454ade84346f59e8d40665f878b2e",
                "revision_number": 1,
                "router:external": False,
                "shared": False,
                "status": "ACTIVE",
                "subnets": [
                        "54d6f61d-db07-451c-9ab3-b9609b6b6f0b"
                ],
                "tenant_id": "4fd44f30292945e481c7b8a0c8908869",
                "updated_at": "2016-03-08T20:19:41",
                "vlan_transparent": True,
                "description": "",
                "is_default": False
            },
            {
                "admin_state_up": True,
                "availability_zone_hints": [],
                "availability_zones": [
                    "nova"
                ],
                "created_at": "2016-03-08T20:19:41",
                "dns_domain": "my-domain.org.",
                "id": "db193ab3-96e3-4cb3-8fc5-05f4296d0324",
                "ipv4_address_scope": None,
                "ipv6_address_scope": None,
                "l2_adjacency": False,
                "mtu": 0,
                "name": "net2",
                "port_security_enabled": True,
                "project_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
                "qos_policy_id": "bfdb6c39f71e4d44b1dfbda245c50819",
                "revision_number": 3,
                "router:external": False,
                "shared": False,
                "status": "ACTIVE",
                "subnets": [
                        "08eae331-0402-425a-923c-34f7cfe39c1b"
                ],
                "tenant_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
                "updated_at": "2016-03-08T20:19:41",
                "vlan_transparent": False,
                "description": "",
                "is_default": False
            }
        ]
    }

    FAKE_NETWORK_ID = "d32019d3-bc6e-4319-9c1d-6722fc136a22"

    FAKE_NETWORK1 = {
        "name": "net1",
        "admin_state_up": True,
        "qos_policy_id": "6a8454ade84346f59e8d40665f878b2e"
    }

    FAKE_NETWORK2 = {
        "name": "net2",
        "admin_state_up": True,
        "qos_policy_id": "bfdb6c39f71e4d44b1dfbda245c50819"
    }

    FAKE_NETWORKS_REQ = {
        "networks": [
            FAKE_NETWORK1,
            FAKE_NETWORK2
        ]
    }

    FAKE_DHCP_AGENT_NETWORK_ID = "80515c45-651f-4f9a-b82b-2ca8a7301a8d"

    FAKE_DHCP_AGENTS = {
        "agents": [
            {
                "binary": "neutron-dhcp-agent",
                "description": None,
                "admin_state_up": True,
                "heartbeat_timestamp": "2017-06-22 18:29:50",
                "availability_zone": "nova",
                "alive": True,
                "topic": "dhcp_agent",
                "host": "osboxes",
                "ha_state": None,
                "agent_type": "DHCP agent",
                "resource_versions": {},
                "created_at": "2017-06-19 21:39:51",
                "started_at": "2017-06-19 21:39:51",
                "id": "b6cfb7a1-6ac4-4980-993c-9d295d37062e",
                "configurations": {
                    "subnets": 2,
                    "dhcp_lease_duration": 86400,
                    "dhcp_driver": "neutron.agent.linux.dhcp.Dnsmasq",
                    "networks": 1,
                    "log_agent_heartbeats": False,
                    "ports": 3
                }
            }
        ]
    }

    def setUp(self):
        super(TestNetworksClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.networks_client = networks_client.NetworksClient(
            fake_auth, "network", "regionOne")

    def _test_list_networks(self, bytes_body=False):
        self.check_service_client_function(
            self.networks_client.list_networks,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_NETWORKS,
            bytes_body,
            200)

    def _test_create_network(self, bytes_body=False):
        self.check_service_client_function(
            self.networks_client.create_network,
            "tempest.lib.common.rest_client.RestClient.post",
            {"network": self.FAKE_NETWORKS["networks"][0]},
            bytes_body,
            201,
            **self.FAKE_NETWORK1)

    def _test_create_bulk_networks(self, bytes_body=False):
        self.check_service_client_function(
            self.networks_client.create_bulk_networks,
            "tempest.lib.common.rest_client.RestClient.post",
            self.FAKE_NETWORKS,
            bytes_body,
            201,
            networks=self.FAKE_NETWORKS_REQ)

    def _test_show_network(self, bytes_body=False):
        self.check_service_client_function(
            self.networks_client.show_network,
            "tempest.lib.common.rest_client.RestClient.get",
            {"network": self.FAKE_NETWORKS["networks"][0]},
            bytes_body,
            200,
            network_id=self.FAKE_NETWORK_ID)

    def _test_update_network(self, bytes_body=False):
        update_kwargs = {
            "name": "sample_network_5_updated",
            "qos_policy_id": "6a8454ade84346f59e8d40665f878b2e"
        }

        resp_body = {
            "network": copy.deepcopy(
                self.FAKE_NETWORKS["networks"][0]
            )
        }
        resp_body["network"].update(update_kwargs)

        self.check_service_client_function(
            self.networks_client.update_network,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            network_id=self.FAKE_NETWORK_ID,
            **update_kwargs)

    def _test_list_dhcp_agents_on_hosting_network(self, bytes_body=False):
        self.check_service_client_function(
            self.networks_client.list_dhcp_agents_on_hosting_network,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_DHCP_AGENTS,
            bytes_body,
            200,
            network_id=self.FAKE_DHCP_AGENT_NETWORK_ID)

    def test_delete_network(self):
        self.check_service_client_function(
            self.networks_client.delete_network,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            network_id=self.FAKE_NETWORK_ID)

    def test_list_networks_with_str_body(self):
        self._test_list_networks()

    def test_list_networks_with_bytes_body(self):
        self._test_list_networks(bytes_body=True)

    def test_create_network_with_str_body(self):
        self._test_create_network()

    def test_create_network_with_bytes_body(self):
        self._test_create_network(bytes_body=True)

    def test_create_bulk_network_with_str_body(self):
        self._test_create_bulk_networks()

    def test_create_bulk_network_with_bytes_body(self):
        self._test_create_bulk_networks(bytes_body=True)

    def test_show_network_with_str_body(self):
        self._test_show_network()

    def test_show_network_with_bytes_body(self):
        self._test_show_network(bytes_body=True)

    def test_update_network_with_str_body(self):
        self._test_update_network()

    def test_update_network_with_bytes_body(self):
        self._test_update_network(bytes_body=True)

    def test_list_dhcp_agents_on_hosting_network_with_str_body(self):
        self._test_list_dhcp_agents_on_hosting_network()

    def test_list_dhcp_agents_on_hosting_network_with_bytes_body(self):
        self._test_list_dhcp_agents_on_hosting_network(bytes_body=True)
