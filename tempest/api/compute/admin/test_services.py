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
from tempest import exceptions
from tempest.test import attr


class ServicesAdminTestJSON(base.BaseComputeAdminTest):

    """
    Tests Services API. List and Enable/Disable require admin privileges.
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ServicesAdminTestJSON, cls).setUpClass()
        cls.client = cls.os_adm.services_client
        cls.non_admin_client = cls.services_client

    @attr(type='gate')
    def test_list_services(self):
        # List Compute services
        resp, services = self.client.list_services()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(services) >= 2)

    @attr(type=['negative', 'gate'])
    def test_list_services_with_non_admin_user(self):
        # List Compute service with non admin user
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.list_services)


class ServicesAdminTestXML(ServicesAdminTestJSON):
    _interface = 'xml'
