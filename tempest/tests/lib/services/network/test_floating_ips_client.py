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

from tempest.lib.services.network import floating_ips_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestFloatingIPsClient(base.BaseServiceTest):

    FAKE_FLOATING_IPS = {
        "floatingips": [
            {
                "router_id": "d23abc8d-2991-4a55-ba98-2aaea84cc72f",
                "description": "for test",
                "dns_domain": "my-domain.org.",
                "dns_name": "myfip",
                "created_at": "2016-12-21T10:55:50Z",
                "updated_at": "2016-12-21T10:55:53Z",
                "revision_number": 1,
                "project_id": "4969c491a3c74ee4af974e6d800c62de",
                "tenant_id": "4969c491a3c74ee4af974e6d800c62de",
                "floating_network_id": "376da547-b977-4cfe-9cba-275c80debf57",
                "fixed_ip_address": "10.0.0.3",
                "floating_ip_address": "172.24.4.228",
                "port_id": "ce705c24-c1ef-408a-bda3-7bbd946164ab",
                "id": "2f245a7b-796b-4f26-9cf9-9e82d248fda7",
                "status": "ACTIVE",
                "port_details": {
                    "status": "ACTIVE",
                    "name": "",
                    "admin_state_up": True,
                    "network_id": "02dd8479-ef26-4398-a102-d19d0a7b3a1f",
                    "device_owner": "compute:nova",
                    "mac_address": "fa:16:3e:b1:3b:30",
                    "device_id": "8e3941b4-a6e9-499f-a1ac-2a4662025cba"
                },
                "tags": ["tag1,tag2"],
                "port_forwardings": []
            },
            {
                "router_id": None,
                "description": "for test",
                "dns_domain": "my-domain.org.",
                "dns_name": "myfip2",
                "created_at": "2016-12-21T11:55:50Z",
                "updated_at": "2016-12-21T11:55:53Z",
                "revision_number": 2,
                "project_id": "4969c491a3c74ee4af974e6d800c62de",
                "tenant_id": "4969c491a3c74ee4af974e6d800c62de",
                "floating_network_id": "376da547-b977-4cfe-9cba-275c80debf57",
                "fixed_ip_address": None,
                "floating_ip_address": "172.24.4.227",
                "port_id": None,
                "id": "61cea855-49cb-4846-997d-801b70c71bdd",
                "status": "DOWN",
                "port_details": None,
                "tags": ["tag1,tag2"],
                "port_forwardings": []
            }
        ]
    }

    FAKE_FLOATING_IP_ID = "2f245a7b-796b-4f26-9cf9-9e82d248fda7"

    def setUp(self):
        super(TestFloatingIPsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.floating_ips_client = floating_ips_client.FloatingIPsClient(
            fake_auth, "compute", "regionOne")

    def _test_list_floatingips(self, bytes_body=False):
        self.check_service_client_function(
            self.floating_ips_client.list_floatingips,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_FLOATING_IPS,
            bytes_body,
            200)

    def _test_create_floatingip(self, bytes_body=False):
        self.check_service_client_function(
            self.floating_ips_client.create_floatingip,
            "tempest.lib.common.rest_client.RestClient.post",
            {"floatingip": self.FAKE_FLOATING_IPS["floatingips"][1]},
            bytes_body,
            201,
            floating_network_id="172.24.4.228")

    def _test_show_floatingip(self, bytes_body=False):
        self.check_service_client_function(
            self.floating_ips_client.show_floatingip,
            "tempest.lib.common.rest_client.RestClient.get",
            {"floatingip": self.FAKE_FLOATING_IPS["floatingips"][0]},
            bytes_body,
            200,
            floatingip_id=self.FAKE_FLOATING_IP_ID)

    def _test_update_floatingip(self, bytes_body=False):
        update_kwargs = {
            "port_id": "fc861431-0e6c-4842-a0ed-e2363f9bc3a8"
        }

        resp_body = {
            "floatingip": copy.deepcopy(
                self.FAKE_FLOATING_IPS["floatingips"][0]
            )
        }
        resp_body["floatingip"].update(update_kwargs)

        self.check_service_client_function(
            self.floating_ips_client.update_floatingip,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            floatingip_id=self.FAKE_FLOATING_IP_ID,
            **update_kwargs)

    def test_list_floatingips_with_str_body(self):
        self._test_list_floatingips()

    def test_list_floatingips_with_bytes_body(self):
        self._test_list_floatingips(bytes_body=True)

    def test_create_floatingip_with_str_body(self):
        self._test_create_floatingip()

    def test_create_floatingip_with_bytes_body(self):
        self._test_create_floatingip(bytes_body=True)

    def test_show_floatingips_with_str_body(self):
        self._test_show_floatingip()

    def test_show_floatingips_with_bytes_body(self):
        self._test_show_floatingip(bytes_body=True)

    def test_update_floatingip_with_str_body(self):
        self._test_update_floatingip()

    def test_update_floatingip_with_bytes_body(self):
        self._test_update_floatingip(bytes_body=True)

    def test_delete_floatingip(self):
        self.check_service_client_function(
            self.floating_ips_client.delete_floatingip,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            floatingip_id=self.FAKE_FLOATING_IP_ID)
