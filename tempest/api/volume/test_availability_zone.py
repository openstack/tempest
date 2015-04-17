# Copyright 2014 NEC Corporation
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

from tempest.api.volume import base
from tempest import test


class AvailabilityZoneV2TestJSON(base.BaseVolumeTest):

    """
    Tests Availability Zone V2 API List
    """

    @classmethod
    def setup_clients(cls):
        super(AvailabilityZoneV2TestJSON, cls).setup_clients()
        cls.client = cls.availability_zone_client

    @test.attr(type='gate')
    @test.idempotent_id('01f1ae88-eba9-4c6b-a011-6f7ace06b725')
    def test_get_availability_zone_list(self):
        # List of availability zone
        availability_zone = self.client.list_availability_zones()
        self.assertTrue(len(availability_zone) > 0)


class AvailabilityZoneV1TestJSON(AvailabilityZoneV2TestJSON):
    _api_version = 1
