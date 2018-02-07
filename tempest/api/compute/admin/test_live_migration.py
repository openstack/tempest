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

import time

from oslo_log import log as logging
import testtools

from tempest.api.compute import base
from tempest.common import compute
from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF
LOG = logging.getLogger(__name__)


class LiveMigrationTest(base.BaseV2ComputeAdminTest):
    max_microversion = '2.24'
    block_migration = None

    @classmethod
    def skip_checks(cls):
        super(LiveMigrationTest, cls).skip_checks()

        if not CONF.compute_feature_enabled.live_migration:
            skip_msg = ("%s skipped as live-migration is "
                        "not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if CONF.compute.min_compute_nodes < 2:
            raise cls.skipException(
                "Less than 2 compute nodes, skipping migration test.")

    @classmethod
    def setup_credentials(cls):
        # These tests don't attempt any SSH validation nor do they use
        # floating IPs on the instance, so all we need is a network and
        # a subnet so the instance being migrated has a single port, but
        # we need that to make sure we are properly updating the port
        # host bindings during the live migration.
        # TODO(mriedem): SSH validation before and after the instance is
        # live migrated would be a nice test wrinkle addition.
        cls.set_network_resources(network=True, subnet=True)
        super(LiveMigrationTest, cls).setup_credentials()

    @classmethod
    def setup_clients(cls):
        super(LiveMigrationTest, cls).setup_clients()
        cls.admin_migration_client = cls.os_admin.migrations_client

    def _migrate_server_to(self, server_id, dest_host, volume_backed=False):
        kwargs = dict()
        block_migration = getattr(self, 'block_migration', None)
        if self.block_migration is None:
            kwargs['disk_over_commit'] = False
            block_migration = (CONF.compute_feature_enabled.
                               block_migration_for_live_migration and
                               not volume_backed)
        self.admin_servers_client.live_migrate_server(
            server_id, host=dest_host, block_migration=block_migration,
            **kwargs)

    def _live_migrate(self, server_id, target_host, state,
                      volume_backed=False):
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
        self.assertEqual(target_host, self.get_host_for_server(server_id),
                         msg)

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
        source_host = self.get_host_for_server(server_id)
        destination_host = self.get_host_other_than(server_id)

        if state == 'PAUSED':
            self.admin_servers_client.pause_server(server_id)
            waiters.wait_for_server_status(self.admin_servers_client,
                                           server_id, state)

        LOG.info("Live migrate from source %s to destination %s",
                 source_host, destination_host)
        self._live_migrate(server_id, destination_host, state, volume_backed)
        if CONF.compute_feature_enabled.live_migrate_back_and_forth:
            # If live_migrate_back_and_forth is enabled it is a grenade job.
            # Therefore test should validate whether LM is compatible in both
            # ways, so live migrate VM back to the source host
            LOG.info("Live migrate back to source %s", source_host)
            self._live_migrate(server_id, source_host, state, volume_backed)

    @decorators.idempotent_id('1dce86b8-eb04-4c03-a9d8-9c1dc3ee0c7b')
    def test_live_block_migration(self):
        self._test_live_migration()

    @decorators.idempotent_id('1e107f21-61b2-4988-8f22-b196e938ab88')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    def test_live_block_migration_paused(self):
        self._test_live_migration(state='PAUSED')

    @testtools.skipUnless(CONF.compute_feature_enabled.
                          volume_backed_live_migration,
                          'Volume-backed live migration not available')
    @decorators.idempotent_id('5071cf17-3004-4257-ae61-73a84e28badd')
    @utils.services('volume')
    def test_volume_backed_live_migration(self):
        self._test_live_migration(volume_backed=True)

    @decorators.idempotent_id('e19c0cc6-6720-4ed8-be83-b6603ed5c812')
    @testtools.skipIf(not CONF.compute_feature_enabled.
                      block_migration_for_live_migration,
                      'Block Live migration not available')
    @testtools.skipIf(not CONF.compute_feature_enabled.
                      block_migrate_cinder_iscsi,
                      'Block Live migration not configured for iSCSI')
    def test_iscsi_volume(self):
        server = self.create_test_server(wait_until="ACTIVE")
        server_id = server['id']
        target_host = self.get_host_other_than(server_id)

        volume = self.create_volume()

        # Attach the volume to the server
        self.attach_volume(server, volume, device='/dev/xvdb')
        server = self.admin_servers_client.show_server(server_id)['server']
        volume_id1 = server["os-extended-volumes:volumes_attached"][0]["id"]
        self._live_migrate(server_id, target_host, 'ACTIVE')

        server = self.admin_servers_client.show_server(server_id)['server']
        volume_id2 = server["os-extended-volumes:volumes_attached"][0]["id"]

        self.assertEqual(volume_id1, volume_id2)


class LiveMigrationRemoteConsolesV26Test(LiveMigrationTest):
    min_microversion = '2.6'
    max_microversion = 'latest'

    @decorators.idempotent_id('6190af80-513e-4f0f-90f2-9714e84955d7')
    @testtools.skipUnless(CONF.compute_feature_enabled.serial_console,
                          'Serial console not supported.')
    @testtools.skipUnless(
        compute.is_scheduler_filter_enabled("DifferentHostFilter"),
        'DifferentHostFilter is not available.')
    def test_live_migration_serial_console(self):
        """Test the live-migration of an instance which has a serial console

        The serial console feature of an instance uses ports on the host.
        These ports need to be updated when they are already in use by
        another instance on the target host. This test checks if this
        update behavior is correctly done, by connecting to the serial
        consoles of the instances before and after the live migration.
        """
        server01_id = self.create_test_server(wait_until='ACTIVE')['id']
        hints = {'different_host': server01_id}
        server02_id = self.create_test_server(scheduler_hints=hints,
                                              wait_until='ACTIVE')['id']
        host01_id = self.get_host_for_server(server01_id)
        host02_id = self.get_host_for_server(server02_id)
        self.assertNotEqual(host01_id, host02_id)

        # At this step we have 2 instances on different hosts, both with
        # serial consoles, both with port 10000 (the default value).
        # https://bugs.launchpad.net/nova/+bug/1455252 describes the issue
        # when live-migrating in such a scenario.

        self._verify_console_interaction(server01_id)
        self._verify_console_interaction(server02_id)

        self._live_migrate(server01_id, host02_id, 'ACTIVE')
        self._verify_console_interaction(server01_id)
        # At this point, both instances have a valid serial console
        # connection, which means the ports got updated.

    def _verify_console_interaction(self, server_id):
        body = self.servers_client.get_remote_console(server_id,
                                                      console_type='serial',
                                                      protocol='serial')
        console_url = body['remote_console']['url']
        data = "test_live_migration_serial_console"
        console_output = ''
        t = 0.0
        interval = 0.1

        ws = compute.create_websocket(console_url)
        try:
            # NOTE (markus_z): It can take a long time until the terminal
            # of the instance is available for interaction. Hence the
            # long timeout value.
            while data not in console_output and t <= 120.0:
                try:
                    ws.send_frame(data)
                    received = ws.receive_frame()
                    console_output += received
                except Exception:
                    # In case we had an issue with send/receive on the
                    # websocket connection, we create a new one.
                    ws = compute.create_websocket(console_url)
                time.sleep(interval)
                t += interval
        finally:
            ws.close()
        self.assertIn(data, console_output)


class LiveAutoBlockMigrationV225Test(LiveMigrationTest):
    min_microversion = '2.25'
    max_microversion = 'latest'
    block_migration = 'auto'
