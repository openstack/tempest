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

from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class ServicesAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Services API. List and Enable/Disable require admin privileges.
    """

    @classmethod
    def resource_setup(cls):
        super(ServicesAdminNegativeTestJSON, cls).resource_setup()
        cls.client = cls.os_adm.services_client
        cls.non_admin_client = cls.services_client

    @test.attr(type=['negative', 'gate'])
    def test_list_services_with_non_admin_user(self):
        self.assertRaises(lib_exc.Unauthorized,
                          self.non_admin_client.list_services)

    @test.attr(type=['negative', 'gate'])
    def test_get_service_by_invalid_params(self):
        # return all services if send the request with invalid parameter
        services = self.client.list_services()
        params = {'xxx': 'nova-compute'}
        services_xxx = self.client.list_services(params)
        self.assertEqual(len(services), len(services_xxx))

    @test.attr(type=['negative', 'gate'])
    def test_get_service_by_invalid_service_and_valid_host(self):
        services = self.client.list_services()
        host_name = services[0]['host']
        params = {'host': host_name, 'binary': 'xxx'}
        services = self.client.list_services(params)
        self.assertEqual(0, len(services))

    @test.attr(type=['negative', 'gate'])
    def test_get_service_with_valid_service_and_invalid_host(self):
        services = self.client.list_services()
        binary_name = services[0]['binary']
        params = {'host': 'xxx', 'binary': binary_name}
        services = self.client.list_services(params)
        self.assertEqual(0, len(services))
