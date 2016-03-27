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
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest import test

CONF = config.CONF


class LiveBlockMigrationTestJSON(base.BaseV2ComputeAdminTest):
    _host_key = 'OS-EXT-SRV-ATTR:host'

    @classmethod
    def skip_checks(cls):
        super(LiveBlockMigrationTestJSON, cls).skip_checks()

        if not CONF.compute_feature_enabled.live_migration:
            skip_msg = ("%s skipped as live-migration is "
                        "not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if CONF.compute.min_compute_nodes < 2:
            raise cls.skipException(
                "Less than 2 compute nodes, skipping migration test.")

    @classmethod
    def setup_clients(cls):
        super(LiveBlockMigrationTestJSON, cls).setup_clients()
        cls.admin_hosts_client = cls.os_adm.hosts_client
        cls.admin_servers_client = cls.os_adm.servers_client
        cls.admin_migration_client = cls.os_adm.migrations_client

    @classmethod
    def _get_compute_hostnames(cls):
        body = cls.admin_hosts_client.list_hosts()['hosts']
        return [
            host_record['host_name']
            for host_record in body
            if host_record['service'] == 'compute'
        ]

    def _get_server_details(self, server_id):
        body = self.admin_servers_client.show_server(server_id)['server']
        return body

    def _get_host_for_server(self, server_id):
        return self._get_server_details(server_id)[self._host_key]

    def _migrate_server_to(self, server_id, dest_host, volume_backed=False):
        block_migration = (CONF.compute_feature_enabled.
                           block_migration_for_live_migration and
                           not volume_backed)
        body = self.admin_servers_client.live_migrate_server(
            server_id, host=dest_host, block_migration=block_migration,
            disk_over_commit=False)
        return body

    def _get_host_other_than(self, host):
        for target_host in self._get_compute_hostnames():
            if host != target_host:
                return target_host

    def _volume_clean_up(self, server_id, volume_id):
        body = self.volumes_client.show_volume(volume_id)['volume']
        if body['status'] == 'in-use':
            self.servers_client.detach_volume(server_id, volume_id)
            waiters.wait_for_volume_status(self.volumes_client,
                                           volume_id, 'available')
        self.volumes_client.delete_volume(volume_id)

    def _test_live_migration(self, state='ACTIVE', volume_backed=False):
        """Tests live migration between two hosts.

        Requires CONF.compute_feature_enabled.live_migration to be True.

        :param state: The vm_state the migrated server should be in before and
                      after the live migration. Supported values are 'ACTIVE'
                      and 'PAUSED'.
        :param volume_backed: If the instance is volume backed or not. If
                              volume_backed, *block* migration is not used.
        """
        # Live migrate an instance to another host
        server_id = self.create_test_server(wait_until="ACTIVE",
                                            volume_backed=volume_backed)['id']
        actual_host = self._get_host_for_server(server_id)
        target_host = self._get_host_other_than(actual_host)

        if state == 'PAUSED':
            self.admin_servers_client.pause_server(server_id)
            waiters.wait_for_server_status(self.admin_servers_client,
                                           server_id, state)

        self._migrate_server_to(server_id, target_host, volume_backed)
        waiters.wait_for_server_status(self.servers_client, server_id, state)
        migration_list = (self.admin_migration_client.list_migrations()
                          ['migrations'])

        msg = ("Live Migration failed. Migrations list for Instance "
               "%s: [" % server_id)
        for live_migration in migration_list:
            if (live_migration['instance_uuid'] == server_id):
                msg += "\n%s" % live_migration
        msg += "]"
        self.assertEqual(target_host, self._get_host_for_server(server_id),
                         msg)

    @test.idempotent_id('1dce86b8-eb04-4c03-a9d8-9c1dc3ee0c7b')
    def test_live_block_migration(self):
        self._test_live_migration()

    @test.idempotent_id('1e107f21-61b2-4988-8f22-b196e938ab88')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    def test_live_block_migration_paused(self):
        self._test_live_migration(state='PAUSED')

    @decorators.skip_because(bug="1549511",
                             condition=CONF.service_available.neutron)
    @test.idempotent_id('5071cf17-3004-4257-ae61-73a84e28badd')
    @test.services('volume')
    def test_volume_backed_live_migration(self):
        self._test_live_migration(volume_backed=True)

    @test.idempotent_id('e19c0cc6-6720-4ed8-be83-b6603ed5c812')
    @testtools.skipIf(not CONF.compute_feature_enabled.
                      block_migration_for_live_migration,
                      'Block Live migration not available')
    @testtools.skipIf(not CONF.compute_feature_enabled.
                      block_migrate_cinder_iscsi,
                      'Block Live migration not configured for iSCSI')
    def test_iscsi_volume(self):
        server_id = self.create_test_server(wait_until="ACTIVE")['id']
        actual_host = self._get_host_for_server(server_id)
        target_host = self._get_host_other_than(actual_host)

        volume = self.volumes_client.create_volume(
            display_name='test')['volume']

        waiters.wait_for_volume_status(self.volumes_client,
                                       volume['id'], 'available')
        self.addCleanup(self._volume_clean_up, server_id, volume['id'])

        # Attach the volume to the server
        self.servers_client.attach_volume(server_id, volumeId=volume['id'],
                                          device='/dev/xvdb')
        waiters.wait_for_volume_status(self.volumes_client,
                                       volume['id'], 'in-use')

        self._migrate_server_to(server_id, target_host)
        waiters.wait_for_server_status(self.servers_client,
                                       server_id, 'ACTIVE')
        self.assertEqual(target_host, self._get_host_for_server(server_id))
