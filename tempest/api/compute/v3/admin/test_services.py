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
from tempest.test import attr


class ServicesAdminV3TestJSON(base.BaseV3ComputeAdminTest):

    """
    Tests Services API. List and Enable/Disable require admin privileges.
    """

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ServicesAdminV3TestJSON, cls).setUpClass()
        cls.client = cls.services_admin_client

    @attr(type='gate')
    def test_list_services(self):
        resp, services = self.client.list_services()
        self.assertEqual(200, resp.status)
        self.assertNotEqual(0, len(services))

    @attr(type='gate')
    def test_get_service_by_service_binary_name(self):
        binary_name = 'nova-compute'
        params = {'binary': binary_name}
        resp, services = self.client.list_services(params)
        self.assertEqual(200, resp.status)
        self.assertNotEqual(0, len(services))
        for service in services:
            self.assertEqual(binary_name, service['binary'])

    @attr(type='gate')
    def test_get_service_by_host_name(self):
        resp, services = self.client.list_services()
        host_name = services[0]['host']
        services_on_host = [service for service in services if
                            service['host'] == host_name]
        params = {'host': host_name}
        resp, services = self.client.list_services(params)

        # we could have a periodic job checkin between the 2 service
        # lookups, so only compare binary lists.
        s1 = map(lambda x: x['binary'], services)
        s2 = map(lambda x: x['binary'], services_on_host)

        # sort the lists before comparing, to take out dependency
        # on order.
        self.assertEqual(sorted(s1), sorted(s2))

    @attr(type='gate')
    def test_get_service_by_service_and_host_name(self):
        resp, services = self.client.list_services()
        host_name = services[0]['host']
        binary_name = services[0]['binary']
        params = {'host': host_name, 'binary': binary_name}
        resp, services = self.client.list_services(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(services))
        self.assertEqual(host_name, services[0]['host'])
        self.assertEqual(binary_name, services[0]['binary'])


class ServicesAdminV3TestXML(ServicesAdminV3TestJSON):
    _interface = 'xml'
