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

from tempest.lib.services.network import subnets_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestSubnetsClient(base.BaseServiceTest):

    FAKE_SUBNET = {
        "subnet": {
            "name": "",
            "enable_dhcp": True,
            "network_id": "d32019d3-bc6e-4319-9c1d-6722fc136a22",
            "segment_id": None,
            "project_id": "4fd44f30292945e481c7b8a0c8908869",
            "tenant_id": "4fd44f30292945e481c7b8a0c8908869",
            "dns_nameservers": [],
            "allocation_pools": [
                {
                    "start": "192.168.199.2",
                    "end": "192.168.199.254"
                }
            ],
            "host_routes": [],
            "ip_version": 4,
            "gateway_ip": "192.168.199.1",
            "cidr": "192.168.199.0/24",
            "id": "3b80198d-4f7b-4f77-9ef5-774d54e17126",
            "created_at": "2016-10-10T14:35:47Z",
            "description": "",
            "ipv6_address_mode": None,
            "ipv6_ra_mode": None,
            "revision_number": 2,
            "service_types": [],
            "subnetpool_id": None,
            "updated_at": "2016-10-10T14:35:47Z"
        }
    }

    FAKE_UPDATED_SUBNET = {
        "subnet": {
            "name": "my_subnet",
            "enable_dhcp": True,
            "network_id": "db193ab3-96e3-4cb3-8fc5-05f4296d0324",
            "segment_id": None,
            "project_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
            "tenant_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
            "dns_nameservers": [],
            "allocation_pools": [
                {
                    "start": "10.0.0.2",
                    "end": "10.0.0.254"
                }
            ],
            "host_routes": [],
            "ip_version": 4,
            "gateway_ip": "10.0.0.1",
            "cidr": "10.0.0.0/24",
            "id": "08eae331-0402-425a-923c-34f7cfe39c1b",
            "description": ""
        }
    }

    FAKE_SUBNETS = {
        "subnets": [
            {
                "name": "private-subnet",
                "enable_dhcp": True,
                "network_id": "db193ab3-96e3-4cb3-8fc5-05f4296d0324",
                "segment_id": None,
                "project_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
                "tenant_id": "26a7980765d0414dbc1fc1f88cdb7e6e",
                "dns_nameservers": [],
                "allocation_pools": [
                    {
                        "start": "10.0.0.2",
                        "end": "10.0.0.254"
                    }
                ],
                "host_routes": [],
                "ip_version": 4,
                "gateway_ip": "10.0.0.1",
                "cidr": "10.0.0.0/24",
                "id": "08eae331-0402-425a-923c-34f7cfe39c1b",
                "created_at": "2016-10-10T14:35:34Z",
                "description": "",
                "ipv6_address_mode": None,
                "ipv6_ra_mode": None,
                "revision_number": 2,
                "service_types": [],
                "subnetpool_id": None,
                "updated_at": "2016-10-10T14:35:34Z"
            },
            {
                "name": "my_subnet",
                "enable_dhcp": True,
                "network_id": "d32019d3-bc6e-4319-9c1d-6722fc136a22",
                "segment_id": None,
                "project_id": "4fd44f30292945e481c7b8a0c8908869",
                "tenant_id": "4fd44f30292945e481c7b8a0c8908869",
                "dns_nameservers": [],
                "allocation_pools": [
                    {
                        "start": "192.0.0.2",
                        "end": "192.255.255.254"
                    }
                ],
                "host_routes": [],
                "ip_version": 4,
                "gateway_ip": "192.0.0.1",
                "cidr": "192.0.0.0/8",
                "id": "54d6f61d-db07-451c-9ab3-b9609b6b6f0b",
                "created_at": "2016-10-10T14:35:47Z",
                "description": "",
                "ipv6_address_mode": None,
                "ipv6_ra_mode": None,
                "revision_number": 2,
                "service_types": [],
                "subnetpool_id": None,
                "updated_at": "2016-10-10T14:35:47Z"
            }
        ]
    }

    FAKE_BULK_SUBNETS = copy.deepcopy(FAKE_SUBNETS)

    FAKE_SUBNET_ID = "54d6f61d-db07-451c-9ab3-b9609b6b6f0b"

    FAKE_NETWORK_ID = "d32019d3-bc6e-4319-9c1d-6722fc136a22"

    def setUp(self):
        super(TestSubnetsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.subnets_client = subnets_client.SubnetsClient(
            fake_auth, 'compute', 'regionOne')

    def _test_create_subnet(self, bytes_body=False):
        self.check_service_client_function(
            self.subnets_client.create_subnet,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_SUBNET,
            bytes_body,
            201,
            network_id=self.FAKE_NETWORK_ID,
            ip_version=4,
            cidr="192.168.199.0/24")

    def _test_update_subnet(self, bytes_body=False):
        self.check_service_client_function(
            self.subnets_client.update_subnet,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_UPDATED_SUBNET,
            bytes_body,
            200,
            subnet_id=self.FAKE_SUBNET_ID,
            name="fake_updated_subnet_name")

    def _test_show_subnet(self, bytes_body=False):
        self.check_service_client_function(
            self.subnets_client.show_subnet,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SUBNET,
            bytes_body,
            200,
            subnet_id=self.FAKE_SUBNET_ID)

    def _test_list_subnets(self, bytes_body=False):
        self.check_service_client_function(
            self.subnets_client.list_subnets,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_SUBNETS,
            bytes_body,
            200)

    def _test_create_bulk_subnets(self, bytes_body=False):
        kwargs = {
            "subnets": [
                {
                    "cidr": "192.168.199.0/24",
                    "ip_version": 4,
                    "network_id": "e6031bc2-901a-4c66-82da-f4c32ed89406"
                },
                {
                    "cidr": "10.56.4.0/22",
                    "ip_version": 4,
                    "network_id": "64239a54-dcc4-4b39-920b-b37c2144effa"
                }
            ]
        }
        self.check_service_client_function(
            self.subnets_client.create_bulk_subnets,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_SUBNETS,
            bytes_body,
            201,
            **kwargs)

    def test_create_subnet_with_str_body(self):
        self._test_create_subnet()

    def test_create_subnet_with_bytes_body(self):
        self._test_create_subnet(bytes_body=True)

    def test_update_subnet_with_str_body(self):
        self._test_update_subnet()

    def test_update_subnet_with_bytes_body(self):
        self._test_update_subnet(bytes_body=True)

    def test_show_subnet_with_str_body(self):
        self._test_show_subnet()

    def test_show_subnet_with_bytes_body(self):
        self._test_show_subnet(bytes_body=True)

    def test_list_subnets_with_str_body(self):
        self._test_list_subnets()

    def test_list_subnets_with_bytes_body(self):
        self._test_list_subnets(bytes_body=True)

    def test_delete_subnet(self):
        self.check_service_client_function(
            self.subnets_client.delete_subnet,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            subnet_id=self.FAKE_SUBNET_ID)

    def test_create_bulk_subnets_with_str_body(self):
        self._test_create_bulk_subnets()

    def test_create_bulk_subnets_with_bytes_body(self):
        self._test_create_bulk_subnets(bytes_body=True)
