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

from tempest.lib.services.network import ports_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestPortsClient(base.BaseServiceTest):

    FAKE_PORTS = {
        "ports": [
            {
                "admin_state_up": True,
                "allowed_address_pairs": [],
                "data_plane_status": None,
                "description": "",
                "device_id": "9ae135f4-b6e0-4dad-9e91-3c223e385824",
                "device_owner": "network:router_gateway",
                "extra_dhcp_opts": [],
                "fixed_ips": [
                    {
                        "ip_address": "172.24.4.2",
                        "subnet_id": "008ba151-0b8c-4a67-98b5-0d2b87666062"
                    }
                ],
                "id": "d80b1a3b-4fc1-49f3-952e-1e2ab7081d8b",
                "mac_address": "fa:16:3e:58:42:ed",
                "name": "",
                "network_id": "70c1db1f-b701-45bd-96e0-a313ee3430b3",
                "project_id": "",
                "security_groups": [],
                "status": "ACTIVE",
                "tenant_id": ""
            },
            {
                "admin_state_up": True,
                "allowed_address_pairs": [],
                "data_plane_status": None,
                "description": "",
                "device_id": "9ae135f4-b6e0-4dad-9e91-3c223e385824",
                "device_owner": "network:router_interface",
                "extra_dhcp_opts": [],
                "fixed_ips": [
                    {
                        "ip_address": "10.0.0.1",
                        "subnet_id": "288bf4a1-51ba-43b6-9d0a-520e9005db17"
                    }
                ],
                "id": "f71a6703-d6de-4be1-a91a-a570ede1d159",
                "mac_address": "fa:16:3e:bb:3c:e4",
                "name": "",
                "network_id": "f27aa545-cbdd-4907-b0c6-c9e8b039dcc2",
                "project_id": "d397de8a63f341818f198abb0966f6f3",
                "security_groups": [],
                "status": "ACTIVE",
                "tenant_id": "d397de8a63f341818f198abb0966f6f3"
            }
        ]
    }

    FAKE_PORT_ID = "d80b1a3b-4fc1-49f3-952e-1e2ab7081d8b"

    FAKE_PORT1 = {
        "admin_state_up": True,
        "name": "",
        "network_id": "70c1db1f-b701-45bd-96e0-a313ee3430b3"
    }

    FAKE_PORT2 = {
        "admin_state_up": True,
        "name": "",
        "network_id": "f27aa545-cbdd-4907-b0c6-c9e8b039dcc2"
    }

    FAKE_PORTS_REQ = {
        "ports": [
            FAKE_PORT1,
            FAKE_PORT2
        ]
    }

    def setUp(self):
        super(TestPortsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.ports_client = ports_client.PortsClient(
            fake_auth, "network", "regionOne")

    def _test_list_ports(self, bytes_body=False):
        self.check_service_client_function(
            self.ports_client.list_ports,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_PORTS,
            bytes_body,
            200)

    def _test_create_port(self, bytes_body=False):
        self.check_service_client_function(
            self.ports_client.create_port,
            "tempest.lib.common.rest_client.RestClient.post",
            {"port": self.FAKE_PORTS["ports"][0]},
            bytes_body,
            201,
            **self.FAKE_PORT1)

    def _test_create_bulk_ports(self, bytes_body=False):
        self.check_service_client_function(
            self.ports_client.create_bulk_ports,
            "tempest.lib.common.rest_client.RestClient.post",
            self.FAKE_PORTS,
            bytes_body,
            201,
            ports=self.FAKE_PORTS_REQ)

    def _test_show_port(self, bytes_body=False):
        self.check_service_client_function(
            self.ports_client.show_port,
            "tempest.lib.common.rest_client.RestClient.get",
            {"port": self.FAKE_PORTS["ports"][0]},
            bytes_body,
            200,
            port_id=self.FAKE_PORT_ID)

    def _test_update_port(self, bytes_body=False):
        update_kwargs = {
            "admin_state_up": True,
            "device_id": "d90a13da-be41-461f-9f99-1dbcf438fdf2",
            "device_owner": "compute:nova",
            "name": "test-for-port-update"
        }

        resp_body = {
            "port": copy.deepcopy(
                self.FAKE_PORTS["ports"][0]
            )
        }
        resp_body["port"].update(update_kwargs)

        self.check_service_client_function(
            self.ports_client.update_port,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            port_id=self.FAKE_PORT_ID,
            **update_kwargs)

    def test_delete_port(self):
        self.check_service_client_function(
            self.ports_client.delete_port,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            port_id=self.FAKE_PORT_ID)

    def test_list_ports_with_str_body(self):
        self._test_list_ports()

    def test_list_ports_with_bytes_body(self):
        self._test_list_ports(bytes_body=True)

    def test_create_port_with_str_body(self):
        self._test_create_port()

    def test_create_port_with_bytes_body(self):
        self._test_create_port(bytes_body=True)

    def test_create_bulk_port_with_str_body(self):
        self._test_create_bulk_ports()

    def test_create_bulk_port_with_bytes_body(self):
        self._test_create_bulk_ports(bytes_body=True)

    def test_show_port_with_str_body(self):
        self._test_show_port()

    def test_show_port_with_bytes_body(self):
        self._test_show_port(bytes_body=True)

    def test_update_port_with_str_body(self):
        self._test_update_port()

    def test_update_port_with_bytes_body(self):
        self._test_update_port(bytes_body=True)
