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
from tempest import test


class ServicesAdminTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests Services API. List and Enable/Disable require admin privileges.
    """

    @classmethod
    def setup_clients(cls):
        super(ServicesAdminTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.services_client

    @test.attr(type='gate')
    @test.idempotent_id('5be41ef4-53d1-41cc-8839-5c2a48a1b283')
    def test_list_services(self):
        services = self.client.list_services()
        self.assertNotEqual(0, len(services))

    @test.attr(type='gate')
    @test.idempotent_id('f345b1ec-bc6e-4c38-a527-3ca2bc00bef5')
    def test_get_service_by_service_binary_name(self):
        binary_name = 'nova-compute'
        params = {'binary': binary_name}
        services = self.client.list_services(params)
        self.assertNotEqual(0, len(services))
        for service in services:
            self.assertEqual(binary_name, service['binary'])

    @test.attr(type='gate')
    @test.idempotent_id('affb42d5-5b4b-43c8-8b0b-6dca054abcca')
    def test_get_service_by_host_name(self):
        services = self.client.list_services()
        host_name = services[0]['host']
        services_on_host = [service for service in services if
                            service['host'] == host_name]
        params = {'host': host_name}

        services = self.client.list_services(params)

        # we could have a periodic job checkin between the 2 service
        # lookups, so only compare binary lists.
        s1 = map(lambda x: x['binary'], services)
        s2 = map(lambda x: x['binary'], services_on_host)

        # sort the lists before comparing, to take out dependency
        # on order.
        self.assertEqual(sorted(s1), sorted(s2))

    @test.attr(type='gate')
    @test.idempotent_id('39397f6f-37b8-4234-8671-281e44c74025')
    def test_get_service_by_service_and_host_name(self):
        services = self.client.list_services()
        host_name = services[0]['host']
        binary_name = services[0]['binary']
        params = {'host': host_name, 'binary': binary_name}

        services = self.client.list_services(params)
        self.assertEqual(1, len(services))
        self.assertEqual(host_name, services[0]['host'])
        self.assertEqual(binary_name, services[0]['binary'])
