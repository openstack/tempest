# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.test import attr


class AZAdminV3TestJSON(base.BaseV3ComputeAdminTest):

    """
    Tests Availability Zone API List
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(AZAdminV3TestJSON, cls).setUpClass()
        cls.client = cls.availability_zone_admin_client
        cls.non_adm_client = cls.availability_zone_client

    @attr(type='gate')
    def test_get_availability_zone_list(self):
        # List of availability zone
        resp, availability_zone = self.client.get_availability_zone_list()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(availability_zone) > 0)

    @attr(type='gate')
    def test_get_availability_zone_list_detail(self):
        # List of availability zones and available services
        resp, availability_zone = \
            self.client.get_availability_zone_list_detail()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(availability_zone) > 0)

    @attr(type='gate')
    def test_get_availability_zone_list_with_non_admin_user(self):
        # List of availability zone with non-administrator user
        resp, availability_zone = \
            self.non_adm_client.get_availability_zone_list()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(availability_zone) > 0)


class AZAdminV3TestXML(AZAdminV3TestJSON):
    _interface = 'xml'
