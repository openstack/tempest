# Copyright 2013 NEC Corporation.  All rights reserved.
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
from tempest import exceptions
from tempest import test


class AZAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Availability Zone API List
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(AZAdminNegativeTestJSON, cls).setUpClass()
        cls.non_adm_client = cls.availability_zone_client

    @test.attr(type=['negative', 'gate'])
    def test_get_availability_zone_list_detail_with_non_admin_user(self):
        # List of availability zones and available services with
        # non-administrator user
        self.assertRaises(
            exceptions.Unauthorized,
            self.non_adm_client.get_availability_zone_list_detail)


class AZAdminNegativeTestXML(AZAdminNegativeTestJSON):
    _interface = 'xml'
