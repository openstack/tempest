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


class VolumesServicesTestJSON(base.BaseVolumeV1AdminTest):
    """
    Tests Volume Services API.
    volume service list requires admin privileges.
    """
    _interface = "json"

    @classmethod
    def setUpClass(cls):
        super(VolumesServicesTestJSON, cls).setUpClass()
        cls.client = cls.os_adm.volume_services_client
        resp, cls.services = cls.client.list_services()
        cls.host_name = cls.services[0]['host']
        cls.binary_name = cls.services[0]['binary']

    @test.attr(type='gate')
    def test_list_services(self):
        resp, services = self.client.list_services()
        self.assertEqual(200, resp.status)
        self.assertNotEqual(0, len(services))

    @test.attr(type='gate')
    def test_get_service_by_service_binary_name(self):
        params = {'binary': self.binary_name}
        resp, services = self.client.list_services(params)
        self.assertEqual(200, resp.status)
        self.assertNotEqual(0, len(services))
        for service in services:
            self.assertEqual(self.binary_name, service['binary'])

    @test.attr(type='gate')
    def test_get_service_by_host_name(self):
        services_on_host = [service for service in self.services if
                            service['host'] == self.host_name]
        params = {'host': self.host_name}

        resp, services = self.client.list_services(params)

        # we could have a periodic job checkin between the 2 service
        # lookups, so only compare binary lists.
        s1 = map(lambda x: x['binary'], services)
        s2 = map(lambda x: x['binary'], services_on_host)
        # sort the lists before comparing, to take out dependency
        # on order.
        self.assertEqual(sorted(s1), sorted(s2))

    @test.attr(type='gate')
    def test_get_service_by_service_and_host_name(self):
        params = {'host': self.host_name, 'binary': self.binary_name}

        resp, services = self.client.list_services(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(services))
        self.assertEqual(self.host_name, services[0]['host'])
        self.assertEqual(self.binary_name, services[0]['binary'])
