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

from tempest.lib.services.network import subnetpools_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSubnetsClient(base.BaseServiceTest):

    FAKE_SUBNETPOOLS = {
        "subnetpools": [
            {
                "min_prefixlen": "64",
                "address_scope_id": None,
                "default_prefixlen": "64",
                "id": "03f761e6-eee0-43fc-a921-8acf64c14988",
                "max_prefixlen": "64",
                "name": "my-subnet-pool-ipv6",
                "default_quota": None,
                "is_default": False,
                "project_id": "9fadcee8aa7c40cdb2114fff7d569c08",
                "tenant_id": "9fadcee8aa7c40cdb2114fff7d569c08",
                "prefixes": [
                    "2001:db8:0:2::/64",
                    "2001:db8::/63"
                ],
                "ip_version": 6,
                "shared": False,
                "description": "",
                "revision_number": 2
            },
            {
                "min_prefixlen": "24",
                "address_scope_id": None,
                "default_prefixlen": "25",
                "id": "f49a1319-423a-4ee6-ba54-1d95a4f6cc68",
                "max_prefixlen": "30",
                "name": "my-subnet-pool-ipv4",
                "default_quota": None,
                "is_default": False,
                "project_id": "9fadcee8aa7c40cdb2114fff7d569c08",
                "tenant_id": "9fadcee8aa7c40cdb2114fff7d569c08",
                "prefixes": [
                    "10.10.0.0/21",
                    "192.168.0.0/16"
                ],
                "ip_version": 4,
                "shared": False,
                "description": "",
                "revision_number": 2
            }
        ]
    }

    FAKE_SUBNETPOOL_ID = "03f761e6-eee0-43fc-a921-8acf64c14988"

    def setUp(self):
        super(TestSubnetsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.subnetpools_client = subnetpools_client.SubnetpoolsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_subnetpools(self, bytes_body=False):
        self.check_service_client_function(
            self.subnetpools_client.list_subnetpools,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SUBNETPOOLS,
            bytes_body,
            200)

    def _test_create_subnetpool(self, bytes_body=False):
        self.check_service_client_function(
            self.subnetpools_client.create_subnetpool,
            'tempest.lib.common.rest_client.RestClient.post',
            {'subnetpool': self.FAKE_SUBNETPOOLS['subnetpools'][1]},
            bytes_body,
            201,
            name="my-subnet-pool-ipv4",
            prefixes=["192.168.0.0/16", "10.10.0.0/21"])

    def _test_show_subnetpool(self, bytes_body=False):
        self.check_service_client_function(
            self.subnetpools_client.show_subnetpool,
            'tempest.lib.common.rest_client.RestClient.get',
            {'subnetpool': self.FAKE_SUBNETPOOLS['subnetpools'][0]},
            bytes_body,
            200,
            subnetpool_id=self.FAKE_SUBNETPOOL_ID)

    def _test_update_subnetpool(self, bytes_body=False):
        update_kwargs = {
            "name": "my-new-subnetpool-name",
            "prefixes": [
                "2001:db8::/64",
                "2001:db8:0:1::/64",
                "2001:db8:0:2::/64"
            ],
            "min_prefixlen": 64,
            "default_prefixlen": 64,
            "max_prefixlen": 64
        }

        resp_body = {
            'subnetpool': copy.deepcopy(
                self.FAKE_SUBNETPOOLS['subnetpools'][0])
        }
        resp_body['subnetpool'].update(update_kwargs)

        self.check_service_client_function(
            self.subnetpools_client.update_subnetpool,
            'tempest.lib.common.rest_client.RestClient.put',
            resp_body,
            bytes_body,
            200,
            subnetpool_id=self.FAKE_SUBNETPOOL_ID,
            **update_kwargs)

    def test_list_subnetpools_with_str_body(self):
        self._test_list_subnetpools()

    def test_list_subnetpools_with_bytes_body(self):
        self._test_list_subnetpools(bytes_body=True)

    def test_create_subnetpool_with_str_body(self):
        self._test_create_subnetpool()

    def test_create_subnetpool_with_bytes_body(self):
        self._test_create_subnetpool(bytes_body=True)

    def test_show_subnetpool_with_str_body(self):
        self._test_show_subnetpool()

    def test_show_subnetpool_with_bytes_body(self):
        self._test_show_subnetpool(bytes_body=True)

    def test_update_subnet_with_str_body(self):
        self._test_update_subnetpool()

    def test_update_subnet_with_bytes_body(self):
        self._test_update_subnetpool(bytes_body=True)

    def test_delete_subnetpool(self):
        self.check_service_client_function(
            self.subnetpools_client.delete_subnetpool,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            subnetpool_id=self.FAKE_SUBNETPOOL_ID)
