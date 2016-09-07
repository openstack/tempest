# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.lib.services.network import routers_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestRoutersClient(base.BaseServiceTest):
    FAKE_CREATE_ROUTER = {
        "router": {
            "name": u'\u2740(*\xb4\u25e1`*)\u2740',
            "external_gateway_info": {
                "network_id": "8ca37218-28ff-41cb-9b10-039601ea7e6b",
                "enable_snat": True,
                "external_fixed_ips": [
                    {
                        "subnet_id": "255.255.255.0",
                        "ip": "192.168.10.1"
                    }
                ]
            },
            "admin_state_up": True,
            "id": "8604a0de-7f6b-409a-a47c-a1cc7bc77b2e"
        }
    }

    FAKE_UPDATE_ROUTER = {
        "router": {
            "name": u'\u2740(*\xb4\u25e1`*)\u2740',
            "external_gateway_info": {
                "network_id": "8ca37218-28ff-41cb-9b10-039601ea7e6b",
                "enable_snat": True,
                "external_fixed_ips": [
                    {
                        "subnet_id": "255.255.255.0",
                        "ip": "192.168.10.1"
                    }
                ]
            },
            "admin_state_up": False,
            "id": "8604a0de-7f6b-409a-a47c-a1cc7bc77b2e"
        }
    }

    def setUp(self):
        super(TestRoutersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = routers_client.RoutersClient(fake_auth,
                                                   'network', 'regionOne')

    def _test_list_routers(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_routers,
            'tempest.lib.common.rest_client.RestClient.get',
            {"routers": []},
            bytes_body)

    def _test_create_router(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_router,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_ROUTER,
            bytes_body,
            name="another_router", admin_state_up="true", status=201)

    def _test_update_router(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_router,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATE_ROUTER,
            bytes_body,
            router_id="8604a0de-7f6b-409a-a47c-a1cc7bc77b2e",
            admin_state_up=False)

    def test_list_routers_with_str_body(self):
        self._test_list_routers()

    def test_list_routers_with_bytes_body(self):
        self._test_list_routers(bytes_body=True)

    def test_create_router_with_str_body(self):
        self._test_create_router()

    def test_create_router_with_bytes_body(self):
        self._test_create_router(bytes_body=True)

    def test_delete_router(self):
        self.check_service_client_function(
            self.client.delete_router,
            'tempest.lib.common.rest_client.RestClient.delete',
            {}, router_id="1", status=204)

    def test_update_router_with_str_body(self):
        self._test_update_router()

    def test_update_router_with_bytes_body(self):
        self._test_update_router(bytes_body=True)
