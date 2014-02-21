# Copyright 2013 NEC Corporation
# Copyright 2013 IBM Corp.
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


class ServicesAdminNegativeV3Test(base.BaseV3ComputeAdminTest):

    """
    Tests Services API. List and Enable/Disable require admin privileges.
    """

    @classmethod
    def setUpClass(cls):
        super(ServicesAdminNegativeV3Test, cls).setUpClass()
        cls.client = cls.services_admin_client
        cls.non_admin_client = cls.services_client

    @attr(type=['negative', 'gate'])
    def test_list_services_with_non_admin_user(self):
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.list_services)

    @attr(type=['negative', 'gate'])
    def test_get_service_by_invalid_params(self):
        # return all services if send the request with invalid parameter
        resp, services = self.client.list_services()
        params = {'xxx': 'nova-compute'}
        resp, services_xxx = self.client.list_services(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(len(services), len(services_xxx))

    @attr(type=['negative', 'gate'])
    def test_get_service_by_invalid_service_and_valid_host(self):
        resp, services = self.client.list_services()
        host_name = services[0]['host']
        params = {'host': host_name, 'binary': 'xxx'}
        resp, services = self.client.list_services(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(services))

    @attr(type=['negative', 'gate'])
    def test_get_service_with_valid_service_and_invalid_host(self):
        resp, services = self.client.list_services()
        binary_name = services[0]['binary']
        params = {'host': 'xxx', 'binary': binary_name}
        resp, services = self.client.list_services(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(0, len(services))
