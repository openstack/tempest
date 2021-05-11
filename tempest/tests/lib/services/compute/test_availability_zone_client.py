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

from tempest.lib.services.compute import availability_zone_client
from tempest.tests.lib import fake_auth_provider
from tempest.tests.lib.services import base


class TestAvailabilityZoneClient(base.BaseServiceTest):

    FAKE_AVAILABIRITY_ZONE_INFO = {
        "availabilityZoneInfo":
        [
            {
                "zoneState": {
                    "available": True
                },
                "hosts": None,
                "zoneName": '\xf4'
            }
        ]
    }

    def setUp(self):
        super(TestAvailabilityZoneClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = availability_zone_client.AvailabilityZoneClient(
            fake_auth, 'compute', 'regionOne')

    def test_list_availability_zones_with_str_body(self):
        self.check_service_client_function(
            self.client.list_availability_zones,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_AVAILABIRITY_ZONE_INFO)

    def test_list_availability_zones_with_bytes_body(self):
        self.check_service_client_function(
            self.client.list_availability_zones,
            'tempest.lib.common.rest_client.RestClient.get',
            self.FAKE_AVAILABIRITY_ZONE_INFO, to_utf=True)
