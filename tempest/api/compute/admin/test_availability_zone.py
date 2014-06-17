# Copyright 2013 NEC Corporation
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

from tempest.api.compute import base
from tempest import test


class AZAdminV3Test(base.BaseComputeAdminTest):
    """
    Tests Availability Zone API List
    """
    _api_version = 3

    @classmethod
    def setUpClass(cls):
        super(AZAdminV3Test, cls).setUpClass()
        cls.client = cls.os_adm.availability_zone_client

    @test.attr(type='gate')
    def test_get_availability_zone_list(self):
        # List of availability zone
        resp, availability_zone = self.client.get_availability_zone_list()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(availability_zone) > 0)

    @test.attr(type='gate')
    def test_get_availability_zone_list_detail(self):
        # List of availability zones and available services
        resp, availability_zone = \
            self.client.get_availability_zone_list_detail()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(availability_zone) > 0)


class AZAdminV2TestJSON(AZAdminV3Test):
    _api_version = 2


class AZAdminV2TestXML(AZAdminV2TestJSON):
    _interface = 'xml'
