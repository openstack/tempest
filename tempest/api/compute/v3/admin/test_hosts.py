# Copyright 2013 IBM Corp.
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
from tempest.common import tempest_fixtures as fixtures
from tempest import test


class HostsAdminV3Test(base.BaseV3ComputeAdminTest):

    """
    Tests hosts API using admin privileges.
    """

    @classmethod
    def setUpClass(cls):
        super(HostsAdminV3Test, cls).setUpClass()
        cls.client = cls.hosts_admin_client

    @test.attr(type='gate')
    def test_list_hosts(self):
        resp, hosts = self.client.list_hosts()
        self.assertEqual(200, resp.status)
        self.assertTrue(len(hosts) >= 2, str(hosts))

    @test.attr(type='gate')
    def test_list_hosts_with_zone(self):
        self.useFixture(fixtures.LockFixture('availability_zone'))
        resp, hosts = self.client.list_hosts()
        host = hosts[0]
        zone_name = host['zone']
        params = {'zone': zone_name}
        resp, hosts = self.client.list_hosts(params)
        self.assertEqual(200, resp.status)
        self.assertTrue(len(hosts) >= 1)
        self.assertIn(host, hosts)

    @test.attr(type='gate')
    def test_list_hosts_with_a_blank_zone(self):
        # If send the request with a blank zone, the request will be successful
        # and it will return all the hosts list
        params = {'zone': ''}
        resp, hosts = self.client.list_hosts(params)
        self.assertNotEqual(0, len(hosts))
        self.assertEqual(200, resp.status)

    @test.attr(type='gate')
    def test_list_hosts_with_nonexistent_zone(self):
        # If send the request with a nonexistent zone, the request will be
        # successful and no hosts will be retured
        params = {'zone': 'xxx'}
        resp, hosts = self.client.list_hosts(params)
        self.assertEqual(0, len(hosts))
        self.assertEqual(200, resp.status)

    @test.attr(type='gate')
    def test_show_host_detail(self):
        resp, hosts = self.client.list_hosts()
        self.assertEqual(200, resp.status)

        hosts = [host for host in hosts if host['service'] == 'compute']
        self.assertTrue(len(hosts) >= 1)

        for host in hosts:
            hostname = host['host_name']
            resp, resources = self.client.show_host_detail(hostname)
            self.assertEqual(200, resp.status)
            self.assertTrue(len(resources) >= 1)
            host_resource = resources[0]['resource']
            self.assertIsNotNone(host_resource)
            self.assertIsNotNone(host_resource['cpu'])
            self.assertIsNotNone(host_resource['disk_gb'])
            self.assertIsNotNone(host_resource['memory_mb'])
            self.assertIsNotNone(host_resource['project'])
            self.assertEqual(hostname, host_resource['host'])
