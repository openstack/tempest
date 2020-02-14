# Copyright 2018 AT&T Corporation.
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

from tempest.lib.services.network import agents_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestAgentsClient(base.BaseServiceTest):

    FAKE_AGENT_ID = "d32019d3-bc6e-4319-9c1d-6123f4135a88"

    FAKE_LIST_DATA = {
        "agents": [
            {
                "binary": "neutron-dhcp-agent",
                "description": None,
                "availability_zone": "nova",
                "heartbeat_timestamp": "2017-09-12 19:39:56",
                "admin_state_up": True,
                "alive": True,
                "id": "840d5d68-5759-4e9e-812f",
                "topic": "dhcp_agent",
                "host": "agenthost1",
                "agent_type": "DHCP agent",
                "started_at": "2017-09-12 19:35:36",
                "created_at": "2017-09-12 19:35:36",
                "resources_synced": None,
                "configurations": {
                    "subnets": 2,
                    "dhcp_lease_duration": 86400,
                    "dhcp_driver": "neutron.agent",
                    "networks": 1,
                    "log_agent_heartbeats": False,
                    "ports": 3
                }
            }
        ]
    }

    FAKE_SHOW_DATA = {
        "agent": {
            "binary": "neutron-openvswitch-agent",
            "description": None,
            "availability_zone": None,
            "heartbeat_timestamp": "2017-09-12 19:40:38",
            "admin_state_up": True,
            "alive": True,
            "id": "04c62b91-b799-48b7-9cd5-2982db6df9c6",
            "topic": "N/A",
            "host": "agenthost1",
            "agent_type": "Open vSwitch agent",
            "started_at": "2017-09-12 19:35:38",
            "created_at": "2017-09-12 19:35:38",
            "resources_synced": True,
            "configurations": {
                "ovs_hybrid_plug": True,
                "in_distributed_mode": False,
                "datapath_type": "system",
                "vhostuser_socket_dir": "/var/run/openvswitch",
                "tunneling_ip": "172.16.78.191",
                "arp_responder_enabled": False,
                "devices": 0,
                "ovs_capabilities": {
                    "datapath_types": [
                        "netdev",
                        "system"
                    ],
                    "iface_types": [
                        "geneve",
                        "gre",
                        "internal",
                        "ipsec_gre",
                        "lisp",
                        "patch",
                        "stt",
                        "system",
                        "tap",
                        "vxlan"
                    ]
                },
                "log_agent_heartbeats": False,
                "l2_population": False,
                "tunnel_types": [
                    "vxlan"
                ],
                "extensions": [],
                "enable_distributed_routing": False,
                "bridge_mappings": {
                    "public": "br-ex"
                }
            }
        }
    }

    FAKE_UPDATE_DATA = {
        "agent": {
            "description": "My OVS agent for OpenStack"
        }
    }

    def setUp(self):
        super(TestAgentsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.agents_client = agents_client.AgentsClient(
            fake_auth, "network", "regionOne")

    def _test_show_agent(self, bytes_body=False):
        self.check_service_client_function(
            self.agents_client.show_agent,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_SHOW_DATA,
            bytes_body,
            status=200,
            agent_id=self.FAKE_AGENT_ID)

    def _test_update_agent(self, bytes_body=False):
        self.check_service_client_function(
            self.agents_client.update_agent,
            "tempest.lib.common.rest_client.RestClient.put",
            self.FAKE_UPDATE_DATA,
            bytes_body,
            status=200,
            agent_id=self.FAKE_AGENT_ID)

    def _test_list_agents(self, bytes_body=False):
        self.check_service_client_function(
            self.agents_client.list_agents,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_LIST_DATA,
            bytes_body,
            status=200)

    def test_show_agent_with_str_body(self):
        self._test_show_agent()

    def test_show_agent_with_bytes_body(self):
        self._test_show_agent(bytes_body=True)

    def test_update_agent_with_str_body(self):
        self._test_update_agent()

    def test_update_agent_with_bytes_body(self):
        self._test_update_agent(bytes_body=True)

    def test_list_agent_with_str_body(self):
        self._test_list_agents()

    def test_list_agent_with_bytes_body(self):
        self._test_list_agents(bytes_body=True)

    def test_delete_agent(self):
        self.check_service_client_function(
            self.agents_client.delete_agent,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            agent_id=self.FAKE_AGENT_ID)
