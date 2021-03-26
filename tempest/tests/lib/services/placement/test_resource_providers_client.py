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

from tempest.lib.services.placement import resource_providers_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestResourceProvidersClient(base.BaseServiceTest):
    FAKE_RESOURCE_PROVIDER_UUID = '3722a86e-a563-11e9-9abb-c3d41b6d3abf'
    FAKE_ROOT_PROVIDER_UUID = '4a6a57c8-a563-11e9-914e-f3e0478fce53'
    FAKE_RESOURCE_PROVIDER = {
        'generation': 0,
        'name': 'Ceph Storage Pool',
        'uuid': FAKE_RESOURCE_PROVIDER_UUID,
        'parent_provider_uuid': FAKE_ROOT_PROVIDER_UUID,
        'root_provider_uuid': FAKE_ROOT_PROVIDER_UUID
    }

    FAKE_RESOURCE_PROVIDERS = {
        'resource_providers': [FAKE_RESOURCE_PROVIDER]
    }

    FAKE_RESOURCE_PROVIDER_INVENTORIES = {
        'inventories': {
            'DISK_GB': {
                'allocation_ratio': 1.0,
                'max_unit': 35,
                'min_unit': 1,
                'reserved': 0,
                'step_size': 1,
                'total': 35
            }
        },
        'resource_provider_generation': 7
    }

    FAKE_AGGREGATE_UUID = '1166be40-a567-11e9-9f2a-53827f9311fa'
    FAKE_RESOURCE_PROVIDER_AGGREGATES = {
        'aggregates': [FAKE_AGGREGATE_UUID]
    }
    FAKE_RESOURCE_UPDATE_INVENTORIES_RESPONSE = {
        "inventories": {
            "MEMORY_MB": {
                "allocation_ratio": 2.0,
                "max_unit": 16,
                "min_unit": 1,
                "reserved": 0,
                "step_size": 4,
                "total": 128
            },
            "VCPU": {
                "allocation_ratio": 10.0,
                "max_unit": 2147483647,
                "min_unit": 1,
                "reserved": 2,
                "step_size": 1,
                "total": 64
            }
        },
        "resource_provider_generation": 2
    }
    FAKE_RESOURCE_UPDATE_INVENTORIES_REQUEST = {
        "inventories": {
            "MEMORY_MB": {
                "allocation_ratio": 2.0,
                "max_unit": 16,
                "step_size": 4,
                "total": 128
            },
            "VCPU": {
                "allocation_ratio": 10.0,
                "reserved": 2,
                "total": 64
            }
        },
        "resource_provider_generation": 1
    }
    FAKE_RESOURCE_PROVIDER_USAGES = {
        "usages": {
            "VCPU": 2,
            "MEMORY_MB": 1024,
            "DISK_GB": 10
        },
        "resource_provider_generation": 3
    }

    def setUp(self):
        super(TestResourceProvidersClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = resource_providers_client.ResourceProvidersClient(
            fake_auth, 'placement', 'regionOne')

    def _test_list_resource_providers(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_resource_providers,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_RESOURCE_PROVIDERS,
            to_utf=bytes_body,
            status=200
        )

    def test_list_resource_providers_with_bytes_body(self):
        self._test_list_resource_providers()

    def test_list_resource_providers_with_str_body(self):
        self._test_list_resource_providers(bytes_body=True)

    def _test_show_resource_provider(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_resource_provider,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_RESOURCE_PROVIDER,
            to_utf=bytes_body,
            status=200,
            rp_uuid=self.FAKE_RESOURCE_PROVIDER_UUID
        )

    def test_show_resource_provider_with_str_body(self):
        self._test_show_resource_provider()

    def test_show_resource_provider_with_bytes_body(self):
        self._test_show_resource_provider(bytes_body=True)

    def _test_list_resource_provider_inventories(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_resource_provider_inventories,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_RESOURCE_PROVIDER_INVENTORIES,
            to_utf=bytes_body,
            status=200,
            rp_uuid=self.FAKE_RESOURCE_PROVIDER_UUID
        )

    def test_list_resource_provider_inventories_with_str_body(self):
        self._test_list_resource_provider_inventories()

    def test_list_resource_provider_inventories_with_bytes_body(self):
        self._test_list_resource_provider_inventories(bytes_body=True)

    def _test_update_resource_providers_inventories(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_resource_providers_inventories,
            'tempest.lib.common.rest_client.RestClient.put',
            self.FAKE_RESOURCE_UPDATE_INVENTORIES_RESPONSE,
            to_utf=bytes_body,
            status=200,
            rp_uuid=self.FAKE_RESOURCE_PROVIDER_UUID,
            **self.FAKE_RESOURCE_UPDATE_INVENTORIES_REQUEST
        )

    def test_update_resource_providers_inventories_with_str_body(self):
        self._test_update_resource_providers_inventories()

    def test_update_resource_providers_inventories_with_bytes_body(self):
        self._test_update_resource_providers_inventories(bytes_body=True)

    def test_delete_resource_providers_inventories(self):
        self.check_service_client_function(
            self.client.delete_resource_providers_inventories,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            status=204,
            rp_uuid=self.FAKE_RESOURCE_PROVIDER_UUID,
        )

    def _test_list_resource_provider_aggregates(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_resource_provider_aggregates,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_RESOURCE_PROVIDER_AGGREGATES,
            to_utf=bytes_body,
            status=200,
            rp_uuid=self.FAKE_RESOURCE_PROVIDER_UUID
        )

    def test_list_resource_provider_aggregates_with_str_body(self):
        self._test_list_resource_provider_aggregates()

    def test_list_resource_provider_aggregates_with_bytes_body(self):
        self._test_list_resource_provider_aggregates(bytes_body=True)

    def _test_list_resource_provider_usages(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_resource_provider_usages,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_RESOURCE_PROVIDER_USAGES,
            to_utf=bytes_body,
            status=200,
            rp_uuid=self.FAKE_RESOURCE_PROVIDER_UUID
        )

    def test_show_resource_provider_usages_with_str_body(self):
        self._test_list_resource_provider_inventories()

    def test_show_resource_provider_usages_with_with_bytes_body(self):
        self._test_list_resource_provider_inventories(bytes_body=True)
