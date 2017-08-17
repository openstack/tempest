# Copyright 2016 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from tempest.lib.services.identity.v3 import regions_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestRegionsClient(base.BaseServiceTest):
    FAKE_CREATE_REGION = {
        "region": {
            "description": "My subregion",
            "id": "RegionOneSubRegion",
            "parent_region_id": "RegionOne"
            }
        }

    FAKE_REGION_INFO = {
        "region": {
            "description": "My subregion 3",
            "id": "RegionThree",
            "links": {
                "self": "http://example.com/identity/v3/regions/RegionThree"
                },
            "parent_region_id": "RegionOne"
            }
        }

    FAKE_LIST_REGIONS = {
        "links": {
            "next": None,
            "previous": None,
            "self": "http://example.com/identity/v3/regions"
            },
        "regions": [
            {
                "description": "",
                "id": "RegionOne",
                "links": {
                    "self": "http://example.com/identity/v3/regions/RegionOne"
                    },
                "parent_region_id": None
                }
            ]
        }

    def setUp(self):
        super(TestRegionsClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = regions_client.RegionsClient(fake_auth, 'identity',
                                                   'regionOne')

    def _test_create_region(self, bytes_body=False):
        self.check_service_client_function(
            self.client.create_region,
            'tempest.lib.common.rest_client.RestClient.post',
            self.FAKE_CREATE_REGION,
            bytes_body,
            status=201)

    def _test_show_region(self, bytes_body=False):
        self.check_service_client_function(
            self.client.show_region,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_REGION_INFO,
            bytes_body,
            region_id="RegionThree")

    def _test_list_regions(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_regions,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_LIST_REGIONS,
            bytes_body)

    def _test_update_region(self, bytes_body=False):
        self.check_service_client_function(
            self.client.update_region,
            'tempest.lib.common.rest_client.RestClient.patch',
            self.FAKE_REGION_INFO,
            bytes_body,
            region_id="RegionThree")

    def test_create_region_with_str_body(self):
        self._test_create_region()

    def test_create_region_with_bytes_body(self):
        self._test_create_region(bytes_body=True)

    def test_show_region_with_str_body(self):
        self._test_show_region()

    def test_show_region_with_bytes_body(self):
        self._test_show_region(bytes_body=True)

    def test_list_regions_with_str_body(self):
        self._test_list_regions()

    def test_list_regions_with_bytes_body(self):
        self._test_list_regions(bytes_body=True)

    def test_update_region_with_str_body(self):
        self._test_update_region()

    def test_update_region_with_bytes_body(self):
        self._test_update_region(bytes_body=True)

    def test_delete_region(self):
        self.check_service_client_function(
            self.client.delete_region,
            'tempest.lib.common.rest_client.RestClient.delete',
            {},
            region_id="RegionThree",
            status=204)
