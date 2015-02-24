# Copyright 2012 OpenStack Foundation
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


import testtools

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class LiveBlockMigrationTestJSON(base.BaseV2ComputeAdminTest):
    _host_key = 'OS-EXT-SRV-ATTR:host'

    @classmethod
    def setup_clients(cls):
        super(LiveBlockMigrationTestJSON, cls).setup_clients()
        cls.admin_hosts_client = cls.os_adm.hosts_client
        cls.admin_servers_client = cls.os_adm.servers_client

    @classmethod
    def resource_setup(cls):
        super(LiveBlockMigrationTestJSON, cls).resource_setup()

        cls.created_server_ids = []

    def _get_compute_hostnames(self):
        body = self.admin_hosts_client.list_hosts()
        return [
            host_record['host_name']
            for host_record in body
            if host_record['service'] == 'compute'
        ]

    def _get_server_details(self, server_id):
        body = self.admin_servers_client.get_server(server_id)
        return body

    def _get_host_for_server(self, server_id):
        return self._get_server_details(server_id)[self._host_key]

    def _migrate_server_to(self, server_id, dest_host):
        body = self.admin_servers_client.live_migrate_server(
            server_id, dest_host,
            CONF.compute_feature_enabled.block_migration_for_live_migration)
        return body

    def _get_host_other_than(self, host):
        for target_host in self._get_compute_hostnames():
            if host != target_host:
                return target_host

    def _get_server_status(self, server_id):
        return self._get_server_details(server_id)['status']

    def _get_an_active_server(self):
        for server_id in self.created_server_ids:
            if 'ACTIVE' == self._get_server_status(server_id):
                return server_id
        else:
            server = self.create_test_server(wait_until="ACTIVE")
            server_id = server['id']
            self.created_server_ids.append(server_id)
            return server_id

    def _volume_clean_up(self, server_id, volume_id):
        body = self.volumes_client.get_volume(volume_id)
        if body['status'] == 'in-use':
            self.servers_client.detach_volume(server_id, volume_id)
            self.volumes_client.wait_for_volume_status(volume_id, 'available')
        self.volumes_client.delete_volume(volume_id)

    @test.idempotent_id('1dce86b8-eb04-4c03-a9d8-9c1dc3ee0c7b')
    @testtools.skipIf(not CONF.compute_feature_enabled.live_migration,
                      'Live migration not available')
    @test.attr(type='gate')
    def test_live_block_migration(self):
        # Live block migrate an instance to another host
        if len(self._get_compute_hostnames()) < 2:
            raise self.skipTest(
                "Less than 2 compute nodes, skipping migration test.")
        server_id = self._get_an_active_server()
        actual_host = self._get_host_for_server(server_id)
        target_host = self._get_host_other_than(actual_host)
        self._migrate_server_to(server_id, target_host)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')
        self.assertEqual(target_host, self._get_host_for_server(server_id))

    @test.idempotent_id('e19c0cc6-6720-4ed8-be83-b6603ed5c812')
    @testtools.skipIf(not CONF.compute_feature_enabled.live_migration or not
                      CONF.compute_feature_enabled.
                      block_migration_for_live_migration,
                      'Block Live migration not available')
    @testtools.skipIf(not CONF.compute_feature_enabled.
                      block_migrate_cinder_iscsi,
                      'Block Live migration not configured for iSCSI')
    @test.attr(type='gate')
    def test_iscsi_volume(self):
        # Live block migrate an instance to another host
        if len(self._get_compute_hostnames()) < 2:
            raise self.skipTest(
                "Less than 2 compute nodes, skipping migration test.")
        server_id = self._get_an_active_server()
        actual_host = self._get_host_for_server(server_id)
        target_host = self._get_host_other_than(actual_host)

        volume = self.volumes_client.create_volume(display_name='test')

        self.volumes_client.wait_for_volume_status(volume['id'],
                                                   'available')
        self.addCleanup(self._volume_clean_up, server_id, volume['id'])

        # Attach the volume to the server
        self.servers_client.attach_volume(server_id, volume['id'],
                                          device='/dev/xvdb')
        self.volumes_client.wait_for_volume_status(volume['id'], 'in-use')

        self._migrate_server_to(server_id, target_host)
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')
        self.assertEqual(target_host, self._get_host_for_server(server_id))
