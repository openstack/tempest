# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import random
import string

import testtools

from tempest.common.utils.linux.remote_client import RemoteClient
from tempest import config
from tempest import exceptions
from tempest.services.compute.json.hosts_client import HostsClientJSON
from tempest.services.compute.json.servers_client import ServersClientJSON
from tempest.test import attr
from tempest.tests.compute import base


@attr(category='live-migration')
class LiveBlockMigrationTest(base.BaseComputeTest):

    live_migration_available = (
        config.TempestConfig().compute.live_migration_available)
    use_block_migration_for_live_migration = (
        config.TempestConfig().compute.use_block_migration_for_live_migration)
    run_ssh = config.TempestConfig().compute.run_ssh

    @classmethod
    def setUpClass(cls):
        super(LiveBlockMigrationTest, cls).setUpClass()

        tenant_name = cls.config.compute_admin.tenant_name
        cls.admin_hosts_client = HostsClientJSON(
            *cls._get_client_args(), tenant_name=tenant_name)

        cls.admin_servers_client = ServersClientJSON(
            *cls._get_client_args(), tenant_name=tenant_name)

        cls.created_server_ids = []

    def _get_compute_hostnames(self):
        _resp, body = self.admin_hosts_client.list_hosts()
        return [
            host_record['host_name']
            for host_record in body
            if host_record['service'] == 'compute'
        ]

    def _get_server_details(self, server_id):
        _resp, body = self.admin_servers_client.get_server(server_id)
        return body

    def _get_host_for_server(self, server_id):
        return self._get_server_details(server_id)['OS-EXT-SRV-ATTR:host']

    def _migrate_server_to(self, server_id, dest_host):
        _resp, body = self.admin_servers_client.live_migrate_server(
            server_id, dest_host, self.use_block_migration_for_live_migration)
        return body

    def _get_host_other_than(self, host):
        for target_host in self._get_compute_hostnames():
            if host != target_host:
                return target_host

    def _get_non_existing_host_name(self):
        random_name = ''.join(
            random.choice(string.ascii_uppercase) for x in range(20))

        self.assertNotIn(random_name, self._get_compute_hostnames())

        return random_name

    def _get_server_status(self, server_id):
        return self._get_server_details(server_id)['status']

    def _get_an_active_server(self):
        for server_id in self.created_server_ids:
            if 'ACTIVE' == self._get_server_status(server_id):
                return server_id
        else:
            server = self.create_server()
            server_id = server['id']
            self.password = server['adminPass']
            self.password = 'password'
            self.created_server_ids.append(server_id)
            return server_id

    @attr(type='positive')
    @testtools.skipIf(not live_migration_available,
                      'Block Live migration not available')
    def test_001_live_block_migration(self):
        # Live block migrate an instance to another host
        if len(self._get_compute_hostnames()) < 2:
            raise self.skipTest(
                "Less than 2 compute nodes, skipping migration test.")
        server_id = self._get_an_active_server()
        actual_host = self._get_host_for_server(server_id)
        target_host = self._get_host_other_than(actual_host)
        self._migrate_server_to(server_id, target_host)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')
        self.assertEquals(target_host, self._get_host_for_server(server_id))

    @attr(type='positive', bug='lp1051881')
    @testtools.skip('Until bug 1051881 is dealt with.')
    @testtools.skipIf(not live_migration_available,
                      'Block Live migration not available')
    def test_002_invalid_host_for_migration(self):
        # Migrating to an invalid host should not change the status

        server_id = self._get_an_active_server()
        target_host = self._get_non_existing_host_name()

        with self.assertRaises(exceptions.BadRequest) as cm:
            self._migrate_server_to(server_id, target_host)
        self.assertEquals('ACTIVE', self._get_server_status(server_id))

    @classmethod
    def tearDownClass(cls):
        for server_id in cls.created_server_ids:
            cls.servers_client.delete_server(server_id)

        super(LiveBlockMigrationTest, cls).tearDownClass()
