# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
# All Rights Reserved.
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

from tempest.lib.services.volume.v3 import availability_zone_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestAvailabilityZoneClient(base.BaseServiceTest):

    FAKE_AZ_LIST = {
        "availabilityZoneInfo": [
            {
                "zoneState": {
                    "available": True
                },
                "zoneName": "nova"
            }
        ]
    }

    def setUp(self):
        super(TestAvailabilityZoneClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = availability_zone_client.AvailabilityZoneClient(
            fake_auth, 'volume', 'regionOne')

    def _test_list_availability_zones(self, bytes_body=False):
        self.check_service_client_function(
            self.client.list_availability_zones,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_AZ_LIST,
            bytes_body)

    def test_list_availability_zones_with_str_body(self):
        self._test_list_availability_zones()

    def test_list_availability_zones_with_bytes_body(self):
        self._test_list_availability_zones(bytes_body=True)
