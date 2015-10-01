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

import copy

from tempest_lib.tests import fake_auth_provider

from tempest.services.compute.json import availability_zone_client
from tempest.tests.services.compute import base


class TestAvailabilityZoneClient(base.BaseComputeServiceTest):

    FAKE_AZ_INFO = {
        "availabilityZoneInfo":
        [
            {
                "zoneState": {
                    "available": True
                },
                "hosts": None,
                "zoneName": u'\xf4'
            }
        ]
    }

    FAKE_AZ_DETAILS = {
        "testhost": {
            "nova-compute": {
                "available": True,
                "active": True,
                "updated_at": "2015-09-10T07:16:46.000000"
            }
        }
    }

    def setUp(self):
        super(TestAvailabilityZoneClient, self).setUp()
        fake_auth = fake_auth_provider.FakeAuthProvider()
        self.client = availability_zone_client.AvailabilityZoneClient(
            fake_auth, 'compute', 'regionOne')

    def _test_availability_zones(self, to_utf=False):
        self.check_service_client_function(
            self.client.list_availability_zones,
            'tempest.common.service_client.ServiceClient.get',
            self.FAKE_AZ_INFO,
            to_utf)

    def _test_availability_zones_with_details(self, to_utf=False):
        fake_az_details = copy.deepcopy(self.FAKE_AZ_INFO)
        fake_az_details['availabilityZoneInfo'][0]['hosts'] = \
            self.FAKE_AZ_DETAILS
        self.check_service_client_function(
            self.client.list_availability_zones,
            'tempest.common.service_client.ServiceClient.get',
            fake_az_details,
            to_utf,
            detail=True)

    def test_list_availability_zones_with_str_body(self):
        self._test_availability_zones()

    def test_list_availability_zones_with_bytes_body(self):
        self._test_availability_zones(True)

    def test_list_availability_zones_with_str_body_and_details(self):
        self._test_availability_zones_with_details()

    def test_list_availability_zones_with_bytes_body_and_details(self):
        self._test_availability_zones_with_details(True)
