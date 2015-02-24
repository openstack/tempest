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


class HostsAdminTestJSON(base.BaseV2ComputeAdminTest):

    """
    Tests hosts API using admin privileges.
    """

    @classmethod
    def setup_clients(cls):
        super(HostsAdminTestJSON, cls).setup_clients()
        cls.client = cls.os_adm.hosts_client

    @test.attr(type='gate')
    @test.idempotent_id('9bfaf98d-e2cb-44b0-a07e-2558b2821e4f')
    def test_list_hosts(self):
        hosts = self.client.list_hosts()
        self.assertTrue(len(hosts) >= 2, str(hosts))

    @test.attr(type='gate')
    @test.idempotent_id('5dc06f5b-d887-47a2-bb2a-67762ef3c6de')
    def test_list_hosts_with_zone(self):
        self.useFixture(fixtures.LockFixture('availability_zone'))
        hosts = self.client.list_hosts()
        host = hosts[0]
        zone_name = host['zone']
        params = {'zone': zone_name}
        hosts = self.client.list_hosts(params)
        self.assertTrue(len(hosts) >= 1)
        self.assertIn(host, hosts)

    @test.attr(type='gate')
    @test.idempotent_id('9af3c171-fbf4-4150-a624-22109733c2a6')
    def test_list_hosts_with_a_blank_zone(self):
        # If send the request with a blank zone, the request will be successful
        # and it will return all the hosts list
        params = {'zone': ''}
        hosts = self.client.list_hosts(params)
        self.assertNotEqual(0, len(hosts))

    @test.attr(type='gate')
    @test.idempotent_id('c6ddbadb-c94e-4500-b12f-8ffc43843ff8')
    def test_list_hosts_with_nonexistent_zone(self):
        # If send the request with a nonexistent zone, the request will be
        # successful and no hosts will be retured
        params = {'zone': 'xxx'}
        hosts = self.client.list_hosts(params)
        self.assertEqual(0, len(hosts))

    @test.attr(type='gate')
    @test.idempotent_id('38adbb12-aee2-4498-8aec-329c72423aa4')
    def test_show_host_detail(self):
        hosts = self.client.list_hosts()

        hosts = [host for host in hosts if host['service'] == 'compute']
        self.assertTrue(len(hosts) >= 1)

        for host in hosts:
            hostname = host['host_name']
            resources = self.client.show_host_detail(hostname)
            self.assertTrue(len(resources) >= 1)
            host_resource = resources[0]['resource']
            self.assertIsNotNone(host_resource)
            self.assertIsNotNone(host_resource['cpu'])
            self.assertIsNotNone(host_resource['disk_gb'])
            self.assertIsNotNone(host_resource['memory_mb'])
            self.assertIsNotNone(host_resource['project'])
            self.assertEqual(hostname, host_resource['host'])
