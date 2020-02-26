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
            "admin_state_up": True,
            "availability_zone_hints": [],
            "availability_zones": [
                "nova"
            ],
            "created_at": "2018-03-19T19:17:04Z",
            "description": "",
            "distributed": False,
            "external_gateway_info": {
                "enable_snat": True,
                "external_fixed_ips": [
                    {
                        "ip_address": "172.24.4.6",
                        "subnet_id": "b930d7f6-ceb7-40a0-8b81-a425dd994ccf"
                    }
                ],
                "network_id": "ae34051f-aa6c-4c75-abf5-50dc9ac99ef3"
            },
            "flavor_id": "f7b14d9a-b0dc-4fbe-bb14-a0f4970a69e0",
            "ha": False,
            "id": "f8a44de0-fc8e-45df-93c7-f79bf3b01c95",
            "name": "router1",
            "routes": [],
            "revision_number": 1,
            "status": "ACTIVE",
            "updated_at": "2018-03-19T19:17:22Z",
            "project_id": "0bd18306d801447bb457a46252d82d13",
            "tenant_id": "0bd18306d801447bb457a46252d82d13",
            "service_type_id": None,
            "tags": ["tag1,tag2"],
            "conntrack_helpers": []
        }
    }

    FAKE_UPDATE_ROUTER = {
        "router": {
            "admin_state_up": True,
            "availability_zone_hints": [],
            "availability_zones": [
                "nova"
            ],
            "created_at": "2018-03-19T19:17:04Z",
            "description": "",
            "distributed": False,
            "external_gateway_info": {
                "enable_snat": True,
                "external_fixed_ips": [
                    {
                        "ip_address": "172.24.4.6",
                        "subnet_id": "b930d7f6-ceb7-40a0-8b81-a425dd994ccf"
                    }
                ],
                "network_id": "ae34051f-aa6c-4c75-abf5-50dc9ac99ef3"
            },
            "flavor_id": "f7b14d9a-b0dc-4fbe-bb14-a0f4970a69e0",
            "ha": False,
            "id": "f8a44de0-fc8e-45df-93c7-f79bf3b01c95",
            "name": "router1",
            "revision_number": 3,
            "routes": [
                {
                    "destination": "179.24.1.0/24",
                    "nexthop": "172.24.3.99"
                }
            ],
            "status": "ACTIVE",
            "updated_at": "2018-03-19T19:17:22Z",
            "project_id": "0bd18306d801447bb457a46252d82d13",
            "tenant_id": "0bd18306d801447bb457a46252d82d13",
            "service_type_id": None,
            "tags": ["tag1,tag2"],
            "conntrack_helpers": []
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
