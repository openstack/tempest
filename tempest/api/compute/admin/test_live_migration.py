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
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exceptions

CONF = config.CONF
LOG = logging.getLogger(__name__)


class LiveMigrationTestBase(base.BaseV2ComputeAdminTest):
    """Test live migration operations supported by admin user"""

    credentials = ['primary', 'admin', 'project_manager']
    create_default_network = True

    @classmethod
    def skip_checks(cls):
        super(LiveMigrationTestBase, cls).skip_checks()

        if not CONF.compute_feature_enabled.live_migration:
            skip_msg = ("%s skipped as live-migration is "
                        "not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        if CONF.compute.min_compute_nodes < 2:
            raise cls.skipException(
                "Less than 2 compute nodes, skipping migration test.")

    @classmethod
    def setup_clients(cls):
        super(LiveMigrationTestBase, cls).setup_clients()
        cls.migration_client = cls.os_admin.migrations_client
        cls.networks_client = cls.os_primary.networks_client
        cls.subnets_client = cls.os_primary.subnets_client
        cls.ports_client = cls.os_primary.ports_client
        cls.trunks_client = cls.os_primary.trunks_client
        cls.mgr_server_client = cls.admin_servers_client

    def _migrate_server_to(self, server_id, dest_host, volume_backed=False,
                           use_manager_client=False):
        kwargs = dict()
        block_migration = getattr(self, 'block_migration', None)
        if self.block_migration is None:
            if self.is_requested_microversion_compatible('2.24'):
                kwargs['disk_over_commit'] = False
            block_migration = (CONF.compute_feature_enabled.
                               block_migration_for_live_migration and
                               not volume_backed)
        if use_manager_client:
            self.mgr_server_client = self.os_project_manager.servers_client
            LOG.info("Using project manager for live migrating server: %s, "
                     "project manager user id: %s",
                     server_id, self.mgr_server_client.user_id)

        self.mgr_server_client.live_migrate_server(
            server_id, host=dest_host, block_migration=block_migration,
            **kwargs)

    def _live_migrate(self, server_id, target_host, state,
                      volume_backed=False):
        # If target_host is None, check whether source host is different with
        # the new host after migration.
        use_manager_client = False
        if target_host is None:
            source_host = self.get_host_for_server(server_id)
            # NOTE(gmaan): If new policy is enforced and and manager role
            # is present in nova then use manager user to live migrate.
            if (CONF.enforce_scope.nova and 'manager' in
                CONF.compute_feature_enabled.nova_policy_roles):
                use_manager_client = True

        self._migrate_server_to(server_id, target_host, volume_backed,
                                use_manager_client)
        waiters.wait_for_server_status(self.servers_client, server_id, state)

        migration_list = (self.os_admin.migrations_client.list_migrations()
                          ['migrations'])

        msg = ("Live Migration failed. Migrations list for Instance "
               "%s: [" % server_id)
        for live_migration in migration_list:
            if (live_migration['instance_uuid'] == server_id):
                msg += "\n%s" % live_migration
        msg += "]"
        if target_host is None:
            self.assertNotEqual(source_host,
                                self.get_host_for_server(server_id), msg)
        else:
            self.assertEqual(target_host, self.get_host_for_server(server_id),
                             msg)


class LiveMigrationTest(LiveMigrationTestBase):
    max_microversion = '2.24'
    block_migration = None
    # If test case want to request the destination host to Nova
    # otherwise Nova scheduler will pick one.
    request_host = True

    @classmethod
    def setup_credentials(cls):
        cls.prepare_instance_network()
        super(LiveMigrationTest, cls).setup_credentials()

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
        if (self.request_host and
            CONF.compute_feature_enabled.can_migrate_between_any_hosts):
            destination_host = self.get_host_other_than(server_id)
        else:
            # not to specify a host so that the scheduler will pick one
            destination_host = None

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

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('1dce86b8-eb04-4c03-a9d8-9c1dc3ee0c7b')
    @testtools.skipUnless(CONF.compute_feature_enabled.
                          block_migration_for_live_migration,
                          'Block Live migration not available')
    def test_live_block_migration(self):
        """Test live migrating an active server"""
        self._test_live_migration()

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('1e107f21-61b2-4988-8f22-b196e938ab88')
    @testtools.skipUnless(CONF.compute_feature_enabled.
                          block_migration_for_live_migration,
                          'Block Live migration not available')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    def test_live_block_migration_paused(self):
        """Test live migrating a paused server"""
        self._test_live_migration(state='PAUSED')

    @decorators.attr(type='multinode')
    @testtools.skipUnless(CONF.compute_feature_enabled.
                          volume_backed_live_migration,
                          'Volume-backed live migration not available')
    @decorators.idempotent_id('5071cf17-3004-4257-ae61-73a84e28badd')
    @utils.services('volume')
    def test_volume_backed_live_migration(self):
        """Test live migrating an active server booted from volume"""
        self._test_live_migration(volume_backed=True)

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('e19c0cc6-6720-4ed8-be83-b6603ed5c812')
    @testtools.skipIf(not CONF.compute_feature_enabled.
                      block_migration_for_live_migration,
                      'Block Live migration not available')
    @utils.services('volume')
    def test_live_block_migration_with_attached_volume(self):
        """Test the live-migration of an instance with an attached volume.

        This tests the live-migration of an instance with both a local disk and
        attach volume. This differs from test_volume_backed_live_migration
        above that tests live-migration with only an attached volume.
        """
        validation_resources = self.get_class_validation_resources(
            self.os_primary)
        server = self.create_test_server(
            validatable=True,
            validation_resources=validation_resources,
            wait_until="SSHABLE")
        server_id = server['id']
        if not CONF.compute_feature_enabled.can_migrate_between_any_hosts:
            # not to specify a host so that the scheduler will pick one
            target_host = None
        else:
            target_host = self.get_host_other_than(server_id)

        volume = self.create_volume()

        # Attach the volume to the server
        self.attach_volume(server, volume, device='/dev/xvdb',
                           wait_for_detach=False)
        server = self.admin_servers_client.show_server(server_id)['server']
        volume_id1 = server["os-extended-volumes:volumes_attached"][0]["id"]
        self._live_migrate(server_id, target_host, 'ACTIVE')

        server = self.admin_servers_client.show_server(server_id)['server']
        volume_id2 = server["os-extended-volumes:volumes_attached"][0]["id"]

        self.assertEqual(volume_id1, volume_id2)

    def _create_net_subnet(self, name, cidr):
        net_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name=name)
        net = self.networks_client.create_network(name=net_name)['network']
        self.addClassResourceCleanup(
            self.networks_client.delete_network, net['id'])

        subnet = self.subnets_client.create_subnet(
            network_id=net['id'],
            cidr=cidr,
            ip_version=4)
        self.addClassResourceCleanup(self.subnets_client.delete_subnet,
                                     subnet['subnet']['id'])
        return net

    def _create_port(self, network_id, name):
        name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name=name)
        port = self.ports_client.create_port(name=name,
                                             network_id=network_id)['port']
        self.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                     self.ports_client.delete_port,
                                     port_id=port['id'])
        return port

    def _create_trunk_with_subport(self):
        tenant_network = self.get_tenant_network()
        parent = self._create_port(network_id=tenant_network['id'],
                                   name='parent')
        net = self._create_net_subnet(name='subport_net', cidr='19.80.0.0/24')
        subport = self._create_port(network_id=net['id'], name='subport')

        trunk = self.trunks_client.create_trunk(
            name=data_utils.rand_name(
                prefix=CONF.resource_name_prefix, name='trunk'),
            port_id=parent['id'],
            sub_ports=[{"segmentation_id": 42, "port_id": subport['id'],
                        "segmentation_type": "vlan"}]
        )['trunk']
        self.addClassResourceCleanup(test_utils.call_and_ignore_notfound_exc,
                                     self.trunks_client.delete_trunk,
                                     trunk['id'])
        return trunk, parent, subport

    def _is_port_status_active(self, port_id):
        port = self.ports_client.show_port(port_id)['port']
        return port['status'] == 'ACTIVE'

    @decorators.unstable_test(bug='2024160')
    @decorators.unstable_test(bug='2033887')
    @decorators.attr(type='multinode')
    @decorators.idempotent_id('0022c12e-a482-42b0-be2d-396b5f0cffe3')
    @utils.requires_ext(service='network', extension='trunk')
    @utils.services('network')
    def test_live_migration_with_trunk(self):
        """Test live migration with trunk and subport"""
        trunk, parent, subport = self._create_trunk_with_subport()

        server = self.create_test_server(
            wait_until="ACTIVE", networks=[{'port': parent['id']}])

        # Wait till subport status is ACTIVE
        self.assertTrue(
            test_utils.call_until_true(
                self._is_port_status_active, CONF.validation.connect_timeout,
                5, subport['id']))
        self.assertTrue(
            test_utils.call_until_true(
                self._is_port_status_active, CONF.validation.connect_timeout,
                5, parent['id']))
        subport = self.ports_client.show_port(subport['id'])['port']

        if not CONF.compute_feature_enabled.can_migrate_between_any_hosts:
            # not to specify a host so that the scheduler will pick one
            target_host = None
        else:
            target_host = self.get_host_other_than(server['id'])

        self._live_migrate(server['id'], target_host, 'ACTIVE')

        # Wait till subport status is ACTIVE
        self.assertTrue(
            test_utils.call_until_true(
                self._is_port_status_active, CONF.validation.connect_timeout,
                5, subport['id']))
        self.assertTrue(
            test_utils.call_until_true(
                self._is_port_status_active, CONF.validation.connect_timeout,
                5, parent['id']))


class LiveMigrationRemoteConsolesV26Test(LiveMigrationTestBase):
    min_microversion = '2.6'
    max_microversion = 'latest'

    @classmethod
    def skip_checks(cls):
        super(LiveMigrationRemoteConsolesV26Test, cls).skip_checks()
        if not CONF.compute_feature_enabled.serial_console:
            skip_msg = ("Serial console not supported.")
            raise cls.skipException(skip_msg)
        if not compute.is_scheduler_filter_enabled("DifferentHostFilter"):
            raise cls.skipException("DifferentHostFilter is not available.")

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('6190af80-513e-4f0f-90f2-9714e84955d7')
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


class LiveMigrationWithoutHostTest(LiveMigrationTest):
    # Test live migrations without host and let Nova scheduler will pick one.
    request_host = False

    @classmethod
    def skip_checks(cls):
        super(LiveMigrationWithoutHostTest, cls).skip_checks()
        if not CONF.compute_feature_enabled.can_migrate_between_any_hosts:
            skip_msg = ("Existing live migration tests are configured to live "
                        "migrate without requesting host.")
            raise cls.skipException(skip_msg)


class LiveMigrationManagerWorkflowTest(LiveMigrationTestBase):
    # This test shows live migrations workflow for the project manager.
    # NOTE(gmaan): microversion 2.80 adds project_id query param in list
    # migration API which is what needed by project manager to request
    # their project migration list.
    min_microversion = '2.80'
    block_migration = None
    request_host = False

    @classmethod
    def skip_checks(cls):
        super(LiveMigrationManagerWorkflowTest, cls).skip_checks()
        # If RBAC new defaults (manager defaults) are not present then we have
        # existing test cases tests the live migration scenarios.
        if (not CONF.enforce_scope.nova or 'manager' not in
            CONF.compute_feature_enabled.nova_policy_roles):
            skip_msg = ("Nova RBAC new defaults are not enabled or manager "
                        "role is not present so skipping the project manager "
                        "specific test.")
            raise cls.skipException(skip_msg)

    @classmethod
    def setup_clients(cls):
        super(LiveMigrationManagerWorkflowTest, cls).setup_clients()
        cls.mgr_server_client = cls.os_project_manager.servers_client
        LOG.info("Using project manager for live migrating servers, "
                 "project manager user id: %s",
                 cls.mgr_server_client.user_id)

    def _initiate_live_migration(self):
        # Project member create the server.
        server_id = self.create_test_server(wait_until="ACTIVE")['id']
        source_host = self.get_host_for_server(server_id)
        # Project manager does not know about host info so they will not
        # specify a host to nova and let nova scheduler to pick one.
        dest_host = None

        LOG.info("Live migrate from source %s", source_host)
        # Live migrate an instance to another host
        self._migrate_server_to(
            server_id, dest_host, use_manager_client=True)
        # Try to list the in-progress live migation. This list can be empty
        # if migration is already completed.
        in_progress_migrations = (
            self.mgr_server_client.list_in_progress_live_migration(
                server_id)['migrations'])
        LOG.info("in-progress live migrations: %s", in_progress_migrations)

        in_progress_migration_uuid = None
        for migration in in_progress_migrations:
            if (migration['server_uuid'] == server_id):
                in_progress_migration_uuid = migration['uuid']
            # Project manager should not get any host related field.
            self.assertIsNone(migration['dest_compute'])
            self.assertIsNone(migration['dest_host'])
            self.assertIsNone(migration['dest_node'])
            self.assertIsNone(migration['source_compute'])
            self.assertIsNone(migration['source_node'])

        return server_id, source_host, in_progress_migration_uuid

    @decorators.attr(type='multinode')
    @decorators.idempotent_id('cc4e2431-4476-49b0-9a80-d7a2f638f091')
    def test_live_migration_by_project_manager(self):
        """Tests live migrations workflow for the project manager.

        - Create server by project member.
        - Project manager perform the below steps:

          * Initiate the live migration.
          * List the in-progress live migration. If migration is completed
            then list might be empty but test does not fail for empty list.
          * Assuming migration is in progress, force complete the live
            migration. Test do not fail if migration is already completed
            and force complete request raise error.
          * Wait for server to be active.
          * List migrations with project_id filter, means request only
            their project migrations. This should return the migration
            initiated by project manager.
          * Check if server is migrated to the differnet host than source
            host.
        """
        server_id, source_host, in_progress_migration_uuid = (
            self._initiate_live_migration())
        try:
            # If we know that migration is in progress then try to force
            # complete it but there is chance that migration might be
            # completed before test send request to nova. In that case,
            # test will not fail. It will skip the force complete and
            # resume to the next step.
            if in_progress_migration_uuid:
                LOG.info("Starting force complete live migrations: %s",
                         in_progress_migration_uuid)
                self.mgr_server_client.force_complete_live_migration(
                    server_id, in_progress_migration_uuid)
                LOG.info("Finish force complete live migrations: %s",
                         in_progress_migration_uuid)
        except lib_exceptions.BadRequest:
            # If migration is already completed then nova will raise
            # HTTPBadRequest. In that case, log the info and execute the
            # rest of the steps.
            LOG.info("Server %s live migration %s is already completed. Due "
                     "to that force completed live migration is not "
                     "performed.", server_id, in_progress_migration_uuid)

        waiters.wait_for_server_status(self.mgr_server_client,
                                       server_id, 'ACTIVE')
        # List migration with project_id as filter so that manager can
        # get its own project migrations.
        mgr_migration_client = self.os_project_manager.migrations_client
        project_id = mgr_migration_client.project_id
        migrations = (mgr_migration_client.list_migrations(
            migration_type='live-migration',
            project_id=project_id)['migrations'])
        migration_uuid = None
        LOG.info("Project %s migrations list: %s", project_id, migrations)
        for migration in migrations:
            if (migration['instance_uuid'] == server_id):
                migration_uuid = migration['uuid']
            # Check if project manager get other project migrations
            self.assertEqual(project_id, migration['project_id'])
            # Project manager should not get any host related field.
            self.assertIsNone(migration['dest_compute'])
            self.assertIsNone(migration['dest_host'])
            self.assertIsNone(migration['dest_node'])
            self.assertIsNone(migration['source_compute'])
            self.assertIsNone(migration['source_node'])
        self.assertIsNotNone(migration_uuid)
        if in_progress_migration_uuid:
            self.assertEqual(in_progress_migration_uuid, migration_uuid)
        msg = ("Server %s Live Migration %s failed.",
               server_id, migration_uuid)
        # Check if server is migrated to the differnet host than source host.
        self.assertNotEqual(source_host,
                            self.get_host_for_server(server_id), msg)
