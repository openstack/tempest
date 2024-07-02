# Copyright (c) 2019 Ericsson
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

from tempest.lib.services.placement import placement_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestPlacementClient(base.BaseServiceTest):
    FAKE_ALLOCATION_CANDIDATES = {
        'allocation_requests': [
            {'allocations': {
                'rp-uuid': {'resources': {'VCPU': 42}}
            }}
        ],
        'provider_summaries': {
            'rp-uuid': {
                'resources': {
                    'VCPU': {'used': 0, 'capacity': 64},
                    'MEMORY_MB': {'capacity': 11196, 'used': 0},
                    'DISK_GB': {'capacity': 19, 'used': 0}
                },
                'traits': ["HW_CPU_X86_SVM"],
            }
        }
    }

    FAKE_ALLOCATIONS = {
        'allocations': {
            'rp-uuid-1': {
                'resources': {
                    'NET_BW_IGR_KILOBIT_PER_SEC': 1
                },
                'generation': 14
            },
            'rp-uuid2': {
                'resources': {
                    'MEMORY_MB': 256,
                    'VCPU': 1
                },
                'generation': 9
            }
        }
    }

    def setUp(self):
        super(TestPlacementClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = placement_client.PlacementClient(
            fake_auth, 'placement', 'regionOne')

    def _test_list_allocation_candidates(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_allocation_candidates,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ALLOCATION_CANDIDATES,
            to_utf=bytes_body,
            **{'resources1': 'NET_BW_IGR_KILOBIT_PER_SEC:1'})

    def test_list_allocation_candidates_with_str_body(self):
        self._test_list_allocation_candidates()

    def test_list_allocation_candidates_with_bytes_body(self):
        self._test_list_allocation_candidates(bytes_body=True)

    def _test_list_allocations(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_allocations,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ALLOCATIONS,
            to_utf=bytes_body,
            **{'consumer_uuid': 'foo-bar'})

    def test_list_allocations_with_str_body(self):
        self._test_list_allocations()

    def test_list_allocations_with_bytes_body(self):
        self._test_list_allocations(bytes_body=True)

    FAKE_ALL_TRAITS = {
        "traits": [
            "CUSTOM_HW_FPGA_CLASS1",
            "CUSTOM_HW_FPGA_CLASS2",
            "CUSTOM_HW_FPGA_CLASS3"
        ]
    }

    FAKE_ASSOCIATED_TRAITS = {
        "traits": [
            "CUSTOM_HW_FPGA_CLASS1",
            "CUSTOM_HW_FPGA_CLASS2"
        ]
    }

    def test_list_traits(self):
        self.check_service_client_function(
            self.client.list_traits,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ALL_TRAITS)

        self.check_service_client_function(
            self.client.list_traits,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ASSOCIATED_TRAITS,
            **{
                "associated": "true"
            })

        self.check_service_client_function(
            self.client.list_traits,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_ALL_TRAITS,
            **{
                "associated": "true",
                "name": "startswith:CUSTOM_HW_FPGPA"
            })

    def test_show_traits(self):
        self.check_service_client_function(
            self.client.show_trait,
            'tempest.lib.common.rest_client.RestClient.get',
            204, status=204,
            name="CUSTOM_HW_FPGA_CLASS1")

        self.check_service_client_function(
            self.client.show_trait,
            'tempest.lib.common.rest_client.RestClient.get',
            404, status=404,
            # trait with this name does not exists
            name="CUSTOM_HW_FPGA_CLASS4")

    def test_create_traits(self):
        self.check_service_client_function(
            self.client.create_trait,
            'tempest.lib.common.rest_client.RestClient.put',
            204, status=204,
            # try to create trait with existing name
            name="CUSTOM_HW_FPGA_CLASS1")

        self.check_service_client_function(
            self.client.create_trait,
            'tempest.lib.common.rest_client.RestClient.put',
            201, status=201,
            # create new trait
            name="CUSTOM_HW_FPGA_CLASS4")

    def test_delete_traits(self):
        self.check_service_client_function(
            self.client.delete_trait,
            'tempest.lib.common.rest_client.RestClient.delete',
            204, status=204,
            name="CUSTOM_HW_FPGA_CLASS1")
