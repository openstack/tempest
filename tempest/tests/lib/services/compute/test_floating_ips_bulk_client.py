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

from tempest.tests.lib import fake_auth_provider

from tempest.lib.services.compute import floating_ips_bulk_client
from tempest.tests.lib.services.compute import base


class TestFloatingIPsBulkClient(base.BaseComputeServiceTest):

    FAKE_FIP_BULK_LIST = {"floating_ip_info": [{
        "address": "10.10.10.1",
        "instance_uuid": None,
        "fixed_ip": None,
        "interface": "eth0",
        "pool": "nova",
        "project_id": None
        },
        {
        "address": "10.10.10.2",
        "instance_uuid": None,
        "fixed_ip": None,
        "interface": "eth0",
        "pool": "nova",
        "project_id": None
        }]}

    def setUp(self):
        super(TestFloatingIPsBulkClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = floating_ips_bulk_client.FloatingIPsBulkClient(
            fake_auth, 'compute', 'regionOne')

    def _test_list_floating_ips_bulk(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_floating_ips_bulk,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_FIP_BULK_LIST,
            to_utf=bytes_body)

    def _test_create_floating_ips_bulk(self, bytes_body=False):
        fake_fip_create_data = {"floating_ips_bulk_create": {
            "ip_range": "192.168.1.0/24", "pool": "nova", "interface": "eth0"}}
        self.check_service_client_function(
            self.client.create_floating_ips_bulk,
            'tempest.lib.common.rest_client.RestClient.post',
            fake_fip_create_data,
            to_utf=bytes_body,
            ip_range="192.168.1.0/24", pool="nova", interface="eth0")

    def _test_delete_floating_ips_bulk(self, bytes_body=False):
        fake_fip_delete_data = {"floating_ips_bulk_delete": "192.168.1.0/24"}
        self.check_service_client_function(
            self.client.delete_floating_ips_bulk,
            'tempest.lib.common.rest_client.RestClient.put',
            fake_fip_delete_data,
            to_utf=bytes_body,
            ip_range="192.168.1.0/24")

    def test_list_floating_ips_bulk_with_str_body(self):
        self._test_list_floating_ips_bulk()

    def test_list_floating_ips_bulk_with_bytes_body(self):
        self._test_list_floating_ips_bulk(True)

    def test_create_floating_ips_bulk_with_str_body(self):
        self._test_create_floating_ips_bulk()

    def test_create_floating_ips_bulk_with_bytes_body(self):
        self._test_create_floating_ips_bulk(True)

    def test_delete_floating_ips_bulk_with_str_body(self):
        self._test_delete_floating_ips_bulk()

    def test_delete_floating_ips_bulk_with_bytes_body(self):
        self._test_delete_floating_ips_bulk(True)
