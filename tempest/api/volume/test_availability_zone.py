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
    def setUpClass(cls):
        super(AvailabilityZoneV2TestJSON, cls).setUpClass()
        cls.client = cls.availability_zone_client

    @test.attr(type='gate')
    def test_get_availability_zone_list(self):
        # List of availability zone
        _, availability_zone = self.client.get_availability_zone_list()
        self.assertTrue(len(availability_zone) > 0)


class AvailabilityZoneV2TestXML(AvailabilityZoneV2TestJSON):
    _interface = 'xml'


class AvailabilityZoneV1TestJSON(AvailabilityZoneV2TestJSON):
    _api_version = 1


class AvailabilityZoneV1TestXML(AvailabilityZoneV1TestJSON):
    _interface = 'xml'
