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
from tempest.lib import decorators


class HostsAdminTestJSON(base.BaseV2ComputeAdminTest):
    """Tests nova hosts API using admin privileges."""

    max_microversion = '2.42'

    @classmethod
    def setup_clients(cls):
        super(HostsAdminTestJSON, cls).setup_clients()
        cls.client = cls.os_admin.hosts_client

    @decorators.idempotent_id('9bfaf98d-e2cb-44b0-a07e-2558b2821e4f')
    def test_list_hosts(self):
        """Listing nova hosts"""
        hosts = self.client.list_hosts()['hosts']
        self.assertGreaterEqual(len(hosts), 2, str(hosts))

    @decorators.idempotent_id('5dc06f5b-d887-47a2-bb2a-67762ef3c6de')
    def test_list_hosts_with_zone(self):
        """Listing nova hosts with specified availability zone"""
        self.useFixture(fixtures.LockFixture('availability_zone'))
        hosts = self.client.list_hosts()['hosts']
        host = hosts[0]
        hosts = self.client.list_hosts(zone=host['zone'])['hosts']
        self.assertNotEmpty(hosts)
        self.assertIn(host, hosts)

    @decorators.idempotent_id('9af3c171-fbf4-4150-a624-22109733c2a6')
    def test_list_hosts_with_a_blank_zone(self):
        """Listing nova hosts with blank availability zone

        If send the request with a blank zone, the request will be successful
        and it will return all the hosts list
        """
        hosts = self.client.list_hosts(zone='')['hosts']
        self.assertNotEmpty(hosts)

    @decorators.idempotent_id('c6ddbadb-c94e-4500-b12f-8ffc43843ff8')
    def test_list_hosts_with_nonexistent_zone(self):
        """Listing nova hosts with not existing availability zone.

        If send the request with a nonexistent zone, the request will be
        successful and no hosts will be returned
        """
        hosts = self.client.list_hosts(zone='xxx')['hosts']
        self.assertEmpty(hosts)

    @decorators.idempotent_id('38adbb12-aee2-4498-8aec-329c72423aa4')
    def test_show_host_detail(self):
        """Showing nova host details"""
        hosts = self.client.list_hosts()['hosts']

        hosts = [host for host in hosts if host['service'] == 'compute']
        self.assertNotEmpty(hosts)

        for host in hosts:
            hostname = host['host_name']
            resources = self.client.show_host(hostname)['host']
            self.assertNotEmpty(resources)
            host_resource = resources[0]['resource']
            self.assertEqual(hostname, host_resource['host'])
