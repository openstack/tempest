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
from tempest.lib import decorators


class ServicesAdminTestJSON(base.BaseV2ComputeAdminTest):
    """Tests Nova Services API.

    List and Enable/Disable require admin privileges.
    """

    @classmethod
    def setup_clients(cls):
        super(ServicesAdminTestJSON, cls).setup_clients()
        cls.client = cls.os_admin.services_client

    @decorators.idempotent_id('5be41ef4-53d1-41cc-8839-5c2a48a1b283')
    def test_list_services(self):
        """Listing nova services"""
        services = self.client.list_services()['services']
        self.assertNotEmpty(services)

    @decorators.idempotent_id('f345b1ec-bc6e-4c38-a527-3ca2bc00bef5')
    def test_get_service_by_service_binary_name(self):
        """Listing nova services by binary name"""
        binary_name = 'nova-compute'
        services = self.client.list_services(binary=binary_name)['services']
        self.assertNotEmpty(services)
        for service in services:
            self.assertEqual(binary_name, service['binary'])

    @decorators.idempotent_id('affb42d5-5b4b-43c8-8b0b-6dca054abcca')
    def test_get_service_by_host_name(self):
        """Listing nova services by host name"""
        services = self.client.list_services()['services']
        host_name = services[0]['host']
        services_on_host = [service for service in services if
                            service['host'] == host_name]

        services = self.client.list_services(host=host_name)['services']

        # we could have a periodic job checkin between the 2 service
        # lookups, so only compare binary lists.
        s1 = map(lambda x: x['binary'], services)
        s2 = map(lambda x: x['binary'], services_on_host)

        # sort the lists before comparing, to take out dependency
        # on order.
        self.assertEqual(sorted(s1), sorted(s2))
