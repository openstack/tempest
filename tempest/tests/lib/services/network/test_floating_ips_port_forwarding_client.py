# Copyright 2021 Red Hat, Inc.
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

from tempest.lib.services.network import floating_ips_port_forwarding_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestFloatingIpsPortForwardingClient(base.BaseServiceTest):

    FAKE_PORT_FORWARDING_REQUEST = {

        "port_forwarding": {
            "protocol": "tcp",
            "internal_ip_address": "10.0.0.11",
            "internal_port": 25,
            "internal_port_id": "1238be08-a2a8-4b8d-addf-fb5e2250e480",
            "external_port": 2230,
            "description": "Some description",
            }

        }

    FAKE_PORT_FORWARDING_RESPONSE = {

        "port_forwarding": {
            "protocol": "tcp",
            "internal_ip_address": "10.0.0.12",
            "internal_port": 26,
            "internal_port_id": "1238be08-a2a8-4b8d-addf-fb5e2250e480",
            "external_port": 2130,
            "description": "Some description",
            "id": "825ade3c-9760-4880-8080-8fc2dbab9acc"
        }
    }

    FAKE_PORT_FORWARDINGS = {
        "port_forwardings": [
            FAKE_PORT_FORWARDING_RESPONSE['port_forwarding']
        ]
    }

    FAKE_FLOATINGIP_ID = "a6800594-5b7a-4105-8bfe-723b346ce866"

    FAKE_PORT_FORWARDING_ID = "a7800594-5b7a-4105-8bfe-723b346ce866"

    def setUp(self):
        super(TestFloatingIpsPortForwardingClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.floating_ips_port_forwarding_client = \
            floating_ips_port_forwarding_client.\
            FloatingIpsPortForwardingClient(fake_auth,
                                            "network",
                                            "regionOne")

    def _test_create_port_forwarding(self, bytes_body=False):
        self.check_service_client_function(
            self.floating_ips_port_forwarding_client.
            create_port_forwarding,
            "tempest.lib.common.rest_client.RestClient.post",
            self.FAKE_PORT_FORWARDING_RESPONSE,
            bytes_body,
            201,
            floatingip_id=self.FAKE_FLOATINGIP_ID,
            **self.FAKE_PORT_FORWARDING_REQUEST)

    def _test_list_port_forwardings(self, bytes_body=False):
        self.check_service_client_function(
            self.floating_ips_port_forwarding_client.
            list_port_forwardings,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_PORT_FORWARDINGS,
            bytes_body,
            200,
            floatingip_id=self.FAKE_FLOATINGIP_ID)

    def _test_show_port_forwardings(self, bytes_body=False):
        self.check_service_client_function(
            self.floating_ips_port_forwarding_client.
            show_port_forwarding,
            "tempest.lib.common.rest_client.RestClient.get",
            self.FAKE_PORT_FORWARDING_RESPONSE,
            bytes_body,
            200,
            floatingip_id=self.FAKE_FLOATINGIP_ID,
            port_forwarding_id=self.FAKE_PORT_FORWARDING_ID)

    def _test_delete_port_forwarding(self):
        self.check_service_client_function(
            self.floating_ips_port_forwarding_client.
            delete_port_forwarding,
            "tempest.lib.common.rest_client.RestClient.delete",
            {},
            status=204,
            floatingip_id=self.FAKE_FLOATINGIP_ID,
            port_forwarding_id=self.FAKE_PORT_FORWARDING_ID)

    def _test_update_port_forwarding(self, bytes_body=False):
        update_kwargs = {
            "internal_port": "27"
        }

        resp_body = {
            "port_forwarding": copy.deepcopy(
                self.FAKE_PORT_FORWARDING_RESPONSE['port_forwarding']
            )
        }
        resp_body["port_forwarding"].update(update_kwargs)

        self.check_service_client_function(
            self.floating_ips_port_forwarding_client.update_port_forwarding,
            "tempest.lib.common.rest_client.RestClient.put",
            resp_body,
            bytes_body,
            200,
            floatingip_id=self.FAKE_FLOATINGIP_ID,
            port_forwarding_id=self.FAKE_PORT_FORWARDING_ID,
            **update_kwargs)

    def test_list_port_forwardings_with_str_body(self):
        self._test_list_port_forwardings()

    def test_list_port_forwardings_with_bytes_body(self):
        self._test_list_port_forwardings(bytes_body=True)

    def test_show_port_forwardings_with_str_body(self):
        self._test_show_port_forwardings()

    def test_show_port_forwardings_with_bytes_body(self):
        self._test_show_port_forwardings(bytes_body=True)

    def test_create_port_forwarding_with_str_body(self):
        self._test_create_port_forwarding()

    def test_create_port_forwarding_with_bytes_body(self):
        self._test_create_port_forwarding(bytes_body=True)

    def test_update_port_forwarding_with_str_body(self):
        self._test_update_port_forwarding()

    def test_update_port_forwarding_with_bytes_body(self):
        self._test_update_port_forwarding(bytes_body=True)
