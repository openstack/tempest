# Copyright 2015 IBM Corp.
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

from tempest.lib.services.compute import hypervisor_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestHypervisorClient(base.BaseServiceTest):

    hypervisor_id = "1"
    hypervisor_name = "hyper.hostname.com"

    def setUp(self):
        super(TestHypervisorClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = hypervisor_client.HypervisorClient(
            fake_auth, 'compute', 'regionOne')

    def test_list_hypervisor_str_body(self):
        self._test_list_hypervisor(bytes_body=False)

    def test_list_hypervisor_byte_body(self):
        self._test_list_hypervisor(bytes_body=True)

    def _test_list_hypervisor(self, bytes_body=False):
        expected = {"hypervisors": [{
            "id": 1,
            "hypervisor_hostname": "hypervisor1.hostname.com"},
            {
            "id": 2,
            "hypervisor_hostname": "hypervisor2.hostname.com"}]}
        self.check_service_client_function(
            self.client.list_hypervisors,
            'tempest.lib.common.rest_client.RestClient.get',
            expected, bytes_body)

    def test_show_hypervisor_str_body(self):
        self._test_show_hypervisor(bytes_body=False)

    def test_show_hypervisor_byte_body(self):
        self._test_show_hypervisor(bytes_body=True)

    def _test_show_hypervisor(self, bytes_body=False):
        expected = {"hypervisor": {
            "cpu_info": "?",
            "current_workload": 0,
            "disk_available_least": 1,
            "host_ip": "10.10.10.10",
            "free_disk_gb": 1028,
            "free_ram_mb": 7680,
            "hypervisor_hostname": "fake-mini",
            "hypervisor_type": "fake",
            "hypervisor_version": 1,
            "id": 1,
            "local_gb": 1028,
            "local_gb_used": 0,
            "memory_mb": 8192,
            "memory_mb_used": 512,
            "running_vms": 0,
            "service": {
                "host": "fake_host",
                "id": 2},
            "vcpus": 1,
            "vcpus_used": 0}}
        self.check_service_client_function(
            self.client.show_hypervisor,
            'tempest.lib.common.rest_client.RestClient.get',
            expected, bytes_body,
            hypervisor_id=self.hypervisor_id)

    def test_list_servers_on_hypervisor_str_body(self):
        self._test_list_servers_on_hypervisor(bytes_body=False)

    def test_list_servers_on_hypervisor_byte_body(self):
        self._test_list_servers_on_hypervisor(bytes_body=True)

    def _test_list_servers_on_hypervisor(self, bytes_body=False):
        expected = {"hypervisors": [{
            "id": 1,
            "hypervisor_hostname": "hyper.hostname.com",
            "servers": [{
                "uuid": "e1ae8fc4-b72d-4c2f-a427-30dd420b6277",
                "name": "instance-00000001"},
                {
                "uuid": "e1ae8fc4-b72d-4c2f-a427-30dd42066666",
                "name": "instance-00000002"}
                ]}
            ]}
        self.check_service_client_function(
            self.client.list_servers_on_hypervisor,
            'tempest.lib.common.rest_client.RestClient.get',
            expected, bytes_body,
            hypervisor_name=self.hypervisor_name)

    def test_show_hypervisor_statistics_str_body(self):
        self._test_show_hypervisor_statistics(bytes_body=False)

    def test_show_hypervisor_statistics_byte_body(self):
        self._test_show_hypervisor_statistics(bytes_body=True)

    def _test_show_hypervisor_statistics(self, bytes_body=False):
        expected = {
            "hypervisor_statistics": {
                "count": 1,
                "current_workload": 0,
                "disk_available_least": 0,
                "free_disk_gb": 1028,
                "free_ram_mb": 7680,
                "local_gb": 1028,
                "local_gb_used": 0,
                "memory_mb": 8192,
                "memory_mb_used": 512,
                "running_vms": 0,
                "vcpus": 1,
                "vcpus_used": 0}}
        self.check_service_client_function(
            self.client.show_hypervisor_statistics,
            'tempest.lib.common.rest_client.RestClient.get',
            expected, bytes_body)

    def test_show_hypervisor_uptime_str_body(self):
        self._test_show_hypervisor_uptime(bytes_body=False)

    def test_show_hypervisor_uptime_byte_body(self):
        self._test_show_hypervisor_uptime(bytes_body=True)

    def _test_show_hypervisor_uptime(self, bytes_body=False):
        expected = {
            "hypervisor": {
                "hypervisor_hostname": "fake-mini",
                "id": 1,
                "uptime": (" 08:32:11 up 93 days, 18:25, 12 users, "
                           " load average: 0.20, 0.12, 0.14")
            }}
        self.check_service_client_function(
            self.client.show_hypervisor_uptime,
            'tempest.lib.common.rest_client.RestClient.get',
            expected, bytes_body,
            hypervisor_id=self.hypervisor_id)

    def test_search_hypervisor_str_body(self):
        self._test_search_hypervisor(bytes_body=False)

    def test_search_hypervisor_byte_body(self):
        self._test_search_hypervisor(bytes_body=True)

    def _test_search_hypervisor(self, bytes_body=False):
        expected = {"hypervisors": [{
            "id": 2,
            "hypervisor_hostname": "hyper.hostname.com"}]}
        self.check_service_client_function(
            self.client.search_hypervisor,
            'tempest.lib.common.rest_client.RestClient.get',
            expected, bytes_body,
            hypervisor_name=self.hypervisor_name)
