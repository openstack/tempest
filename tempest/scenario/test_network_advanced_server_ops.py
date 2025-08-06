# Copyright 2014 IBM Corp.
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

from oslo_log import log
from tempest.common import utils
from tempest.common.utils.linux import remote_client
from tempest.common.utils import net_downtime
from tempest.common import waiters
from tempest import config
from tempest.lib.common import api_version_request
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF

LOG = log.getLogger(__name__)


class BaseTestNetworkAdvancedServerOps(manager.NetworkScenarioTest):
    """Base class for defining methods used in tests."""

    credentials = ['primary', 'admin', 'project_manager']

    @classmethod
    def skip_checks(cls):
        super(BaseTestNetworkAdvancedServerOps, cls).skip_checks()
        if not (CONF.network.project_networks_reachable or
                CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            raise cls.skipException(msg)
        if not CONF.network_feature_enabled.floating_ips:
            raise cls.skipException("Floating ips are not available")

    @classmethod
    def setup_clients(cls):
        super(BaseTestNetworkAdvancedServerOps, cls).setup_clients()
        cls.mgr_server_client = cls.os_admin.servers_client
        cls.sec_group_rules_client = \
            cls.os_primary.security_group_rules_client
        cls.sec_groups_client = cls.os_primary.security_groups_client
        cls.keypairs_client = cls.os_primary.keypairs_client
        cls.floating_ips_client = cls.os_primary.floating_ips_client
        cls.servers_client = cls.os_primary.servers_client

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(BaseTestNetworkAdvancedServerOps, cls).setup_credentials()

    def _setup_server(self, keypair, host_spec=None):
        security_groups = []
        if utils.is_extension_enabled('security-group', 'network'):
            sec_args = {
                'security_group_rules_client':
                self.sec_group_rules_client,
                'security_groups_client':
                self.sec_groups_client
            }
            security_group = self.create_security_group(**sec_args)
            security_groups = [{'name': security_group['name']}]
        network, _, _ = self.setup_network_subnet_with_router()
        server_args = {
            'networks': [{'uuid': network['id']}],
            'key_name': keypair['name'],
            'security_groups': security_groups,
        }

        if host_spec is not None:
            server_args['host'] = host_spec
            # by default, host can be specified by administrators only
            server_args['clients'] = self.os_admin

        server = self.create_server(**server_args)
        return server

    def _setup_network(self, server, keypair):
        public_network_id = CONF.network.public_network_id
        floating_ip = self.create_floating_ip(
            server, public_network_id, client=self.floating_ips_client)
        # Verify that we can indeed connect to the server before we mess with
        # it's state
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

        return floating_ip

    def _check_network_connectivity(self, server, keypair, floating_ip,
                                    should_connect=True,
                                    username=CONF.validation.image_ssh_user):
        private_key = keypair['private_key']
        self.check_tenant_network_connectivity(
            server, username, private_key,
            should_connect=should_connect,
            servers_for_debug=[server])
        floating_ip_addr = floating_ip['floating_ip_address']
        # Check FloatingIP status before checking the connectivity
        self.check_floating_ip_status(floating_ip, 'ACTIVE')
        self.check_vm_connectivity(floating_ip_addr, username,
                                   private_key, should_connect,
                                   'Public network connectivity check failed',
                                   server)

    def _wait_server_status_and_check_network_connectivity(
        self, server, keypair, floating_ip,
        username=CONF.validation.image_ssh_user):
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')
        self._check_network_connectivity(server, keypair, floating_ip,
                                         username=username)

    def _test_server_connectivity_resize(self, src_host=None):
        resize_flavor = CONF.compute.flavor_ref_alt
        keypair = self.create_keypair()
        server = self._setup_server(keypair, src_host)
        if src_host:
            server_host = self.get_host_for_server(server['id'])
            self.assertEqual(server_host, src_host)
        floating_ip = self._setup_network(server, keypair)
        self.servers_client.resize_server(server['id'],
                                          flavor_ref=resize_flavor)
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'VERIFY_RESIZE')
        self.servers_client.confirm_resize_server(server['id'])
        server = self.servers_client.show_server(server['id'])['server']
        # Nova API > 2.46 no longer includes flavor.id, and schema check
        # will cover whether 'id' should be in flavor
        if server['flavor'].get('id'):
            self.assertEqual(resize_flavor, server['flavor']['id'])
        else:
            flavor = self.flavors_client.show_flavor(resize_flavor)['flavor']
            self.assertEqual(flavor['name'], server['flavor']['original_name'])
            for key in ['ram', 'vcpus', 'disk']:
                self.assertEqual(flavor[key], server['flavor'][key])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    def _test_server_connectivity_cold_migration(self, source_host=None,
                                                 dest_host=None):
        keypair = self.create_keypair(client=self.keypairs_client)
        server = self._setup_server(keypair, source_host)
        floating_ip = self._setup_network(server, keypair)
        src_host = self.get_host_for_server(server['id'])
        if source_host:
            self.assertEqual(src_host, source_host)
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

        if (not dest_host and CONF.enforce_scope.nova and 'manager' in
            CONF.compute_feature_enabled.nova_policy_roles):
            self.mgr_server_client = self.os_project_manager.servers_client
            LOG.info("Using project manager for migrating server: %s, "
                     "project manager user id: %s",
                     server['id'], self.mgr_server_client.user_id)
        self.mgr_server_client.migrate_server(
            server['id'], host=dest_host)
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'VERIFY_RESIZE')
        self.servers_client.confirm_resize_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)
        dst_host = self.get_host_for_server(server['id'])
        if dest_host:
            self.assertEqual(dst_host, dest_host)
        self.assertNotEqual(src_host, dst_host)

    def _test_server_connectivity_live_migration(self, source_host=None,
                                                 dest_host=None,
                                                 migration=False):
        keypair = self.create_keypair(client=self.keypairs_client)
        server = self._setup_server(keypair, source_host)
        floating_ip = self._setup_network(server, keypair)
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

        block_migration = (CONF.compute_feature_enabled.
                           block_migration_for_live_migration)
        src_host = self.get_host_for_server(server['id'])
        if source_host:
            self.assertEqual(src_host, source_host)

        downtime_meter = net_downtime.NetDowntimeMeter(
            floating_ip['floating_ip_address'])
        self.useFixture(downtime_meter)

        metadata_downtime_meter = net_downtime.MetadataDowntimeMeter(
            remote_client.RemoteClient(floating_ip['floating_ip_address'],
                                       CONF.validation.image_ssh_user,
                                       pkey=keypair['private_key']))
        self.useFixture(metadata_downtime_meter)

        migration_kwargs = {'host': None, 'block_migration': block_migration}

        # check if microversion is less than 2.25 because of
        # disk_over_commit is depracted since compute api version 2.25
        # if min_microversion is None, it runs on version < 2.25
        min_v = api_version_request.APIVersionRequest(
            CONF.compute.min_microversion)
        api_v = api_version_request.APIVersionRequest('2.25')
        if not migration and (CONF.compute.min_microversion is None or
                              min_v < api_v):
            migration_kwargs['disk_over_commit'] = False

        if dest_host:
            migration_kwargs['host'] = dest_host
        elif (CONF.enforce_scope.nova and 'manager' in
              CONF.compute_feature_enabled.nova_policy_roles):
            self.mgr_server_client = self.os_project_manager.servers_client
            LOG.info("Using project manager for migrating server: %s, "
                     "project manager user id: %s",
                     server['id'], self.mgr_server_client.user_id)
        self.mgr_server_client.live_migrate_server(
            server['id'], **migration_kwargs)
        waiters.wait_for_server_status(self.servers_client,
                                       server['id'], 'ACTIVE')

        dst_host = self.get_host_for_server(server['id'])
        if dest_host:
            self.assertEqual(dst_host, dest_host)

        self.assertNotEqual(src_host, dst_host, 'Server did not migrate')

        # we first wait until the VM replies pings again, then check the
        # network downtime
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

        downtime = downtime_meter.get_downtime()
        self.assertIsNotNone(downtime)
        LOG.debug("Downtime seconds measured with downtime_meter = %r",
                  downtime)
        allowed_downtime = CONF.validation.allowed_network_downtime
        self.assertLessEqual(
            downtime, allowed_downtime,
            "Downtime of {} seconds is higher than expected '{}'".format(
                downtime, allowed_downtime))

        metadata_downtime_results = metadata_downtime_meter.get_results()
        self.assertGreater(metadata_downtime_results['successes'], 0)
        LOG.debug("Metadata Downtime seconds measured = %r",
                  metadata_downtime_results['downtime'])
        allowed_metadata_downtime = CONF.validation.allowed_metadata_downtime
        metadata_downtime_failed = \
            metadata_downtime_results['downtime']['FAILED']
        self.assertLessEqual(
            metadata_downtime_failed, allowed_metadata_downtime,
            "Metadata downtime: {} seconds is higher than expected: {}".format(
                metadata_downtime_failed, allowed_metadata_downtime))

    def _test_server_connectivity_cold_migration_revert(self, source_host=None,
                                                        dest_host=None):
        keypair = self.create_keypair(client=self.keypairs_client)
        server = self._setup_server(keypair, source_host)
        floating_ip = self._setup_network(server, keypair)
        src_host = self.get_host_for_server(server['id'])
        if source_host:
            self.assertEqual(src_host, source_host)
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

        if (not dest_host and CONF.enforce_scope.nova and 'manager' in
            CONF.compute_feature_enabled.nova_policy_roles):
            self.mgr_server_client = self.os_project_manager.servers_client
            LOG.info("Using project manager for migrating server: %s, "
                     "project manager user id: %s",
                     server['id'], self.mgr_server_client.user_id)
        self.mgr_server_client.migrate_server(
            server['id'], host=dest_host)
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'VERIFY_RESIZE')
        if dest_host:
            self.assertEqual(dest_host,
                             self.get_host_for_server(server['id']))
        self.servers_client.revert_resize_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)
        dst_host = self.get_host_for_server(server['id'])

        self.assertEqual(src_host, dst_host)


class TestNetworkAdvancedServerOps(BaseTestNetworkAdvancedServerOps):
    """Check VM connectivity after some advanced instance operations executed:

     * Stop/Start an instance
     * Reboot an instance
     * Rebuild an instance
     * Pause/Unpause an instance
     * Suspend/Resume an instance
    """

    @decorators.idempotent_id('61f1aa9a-1573-410e-9054-afa557cab021')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_server_connectivity_stop_start(self):
        keypair = self.create_keypair()
        server = self._setup_server(keypair)
        floating_ip = self._setup_network(server, keypair)
        self.servers_client.stop_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'SHUTOFF')
        self._check_network_connectivity(server, keypair, floating_ip,
                                         should_connect=False)
        self.servers_client.start_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @decorators.idempotent_id('7b6860c2-afa3-4846-9522-adeb38dfbe08')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_server_connectivity_reboot(self):
        keypair = self.create_keypair()
        server = self._setup_server(keypair)
        floating_ip = self._setup_network(server, keypair)
        self.servers_client.reboot_server(server['id'], type='SOFT')
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @decorators.idempotent_id('88a529c2-1daa-4c85-9aec-d541ba3eb699')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_server_connectivity_rebuild(self):
        keypair = self.create_keypair()
        server = self._setup_server(keypair)
        floating_ip = self._setup_network(server, keypair)
        image_ref_alt = CONF.compute.image_ref_alt
        username_alt = CONF.validation.image_alt_ssh_user
        self.servers_client.rebuild_server(server['id'],
                                           image_ref=image_ref_alt)
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip, username_alt)

    @decorators.idempotent_id('2b2642db-6568-4b35-b812-eceed3fa20ce')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_server_connectivity_pause_unpause(self):
        keypair = self.create_keypair()
        server = self._setup_server(keypair)
        floating_ip = self._setup_network(server, keypair)
        self.servers_client.pause_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'PAUSED')
        self._check_network_connectivity(server, keypair, floating_ip,
                                         should_connect=False)
        self.servers_client.unpause_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @decorators.idempotent_id('5cdf9499-541d-4923-804e-b9a60620a7f0')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_server_connectivity_suspend_resume(self):
        keypair = self.create_keypair()
        server = self._setup_server(keypair)
        floating_ip = self._setup_network(server, keypair)
        self.servers_client.suspend_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'SUSPENDED')
        self._check_network_connectivity(server, keypair, floating_ip,
                                         should_connect=False)
        self.servers_client.resume_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @decorators.idempotent_id('719eb59d-2f42-4b66-b8b1-bb1254473967')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_server_connectivity_resize(self):
        self._test_server_connectivity_resize()

    @decorators.idempotent_id('a4858f6c-401e-4155-9a49-d5cd053d1a2f')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration is not available.')
    @testtools.skipUnless(CONF.compute.min_compute_nodes > 1,
                          'Less than 2 compute nodes, skipping multinode '
                          'tests.')
    @decorators.attr(type=['slow', 'multinode'])
    @utils.services('compute', 'network')
    def test_server_connectivity_cold_migration(self):
        self._test_server_connectivity_cold_migration()

    @decorators.idempotent_id('03fd1562-faad-11e7-9ea0-fa163e65f5ce')
    @testtools.skipUnless(CONF.compute_feature_enabled.live_migration,
                          'Live migration is not available.')
    @testtools.skipUnless(CONF.compute.min_compute_nodes > 1,
                          'Less than 2 compute nodes, skipping multinode '
                          'tests.')
    @decorators.attr(type=['slow', 'multinode'])
    @utils.services('compute', 'network')
    def test_server_connectivity_live_migration(self):
        self._test_server_connectivity_live_migration()

    @decorators.idempotent_id('25b188d7-0183-4b1e-a11d-15840c8e2fd6')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration is not available.')
    @testtools.skipUnless(CONF.compute.min_compute_nodes > 1,
                          'Less than 2 compute nodes, skipping multinode '
                          'tests.')
    @decorators.attr(type=['slow', 'multinode'])
    @utils.services('compute', 'network')
    def test_server_connectivity_cold_migration_revert(self):
        self._test_server_connectivity_cold_migration_revert()


class TestNetworkAdvancedServerMigrationWithHost(
    BaseTestNetworkAdvancedServerOps):

    """Check VM connectivity with specifying source and destination hosts:

    * Resize an instance by creating server on configured source host
    * Migrate server by creating it on configured source host and migrate it
        - Cold Migration
        - Cold Migration with revert
        - Live Migration
    """
    credentials = ['primary', 'admin', 'project_manager']
    compute_min_microversion = "2.74"

    @classmethod
    def skip_checks(cls):
        super(TestNetworkAdvancedServerMigrationWithHost, cls).skip_checks()
        if not (CONF.compute.migration_source_host or
                CONF.compute.migration_dest_host):
            raise cls.skipException("migration_source_host or "
                                    "migration_dest_host is required")
        if (CONF.compute.migration_source_host and
            CONF.compute.migration_dest_host and
            CONF.compute.migration_source_host ==
            CONF.compute.migration_dest_host):
            raise cls.skipException("migration_source_host and "
                                    "migration_dest_host must be different")

    @classmethod
    def setup_clients(cls):
        super(BaseTestNetworkAdvancedServerOps, cls).setup_clients()
        cls.sec_group_rules_client = \
            cls.os_admin.security_group_rules_client
        cls.sec_groups_client = cls.os_admin.security_groups_client
        cls.keypairs_client = cls.os_admin.keypairs_client
        cls.floating_ips_client = cls.os_admin.floating_ips_client
        cls.servers_client = cls.os_admin.servers_client
        cls.mgr_server_client = cls.os_admin.servers_client

    @decorators.idempotent_id('06e23934-79ae-11ee-b962-0242ac120002')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_server_connectivity_resize(self):
        source_host = CONF.compute.migration_source_host
        self._test_server_connectivity_resize(src_host=source_host)

    @decorators.idempotent_id('14f0c9e6-79ae-11ee-b962-0242ac120002')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration is not available.')
    @testtools.skipUnless(CONF.compute.min_compute_nodes > 1,
                          'Less than 2 compute nodes, skipping multinode '
                          'tests.')
    @decorators.attr(type=['slow', 'multinode'])
    @utils.services('compute', 'network')
    def test_server_connectivity_cold_migration(self):
        source_host = CONF.compute.migration_source_host
        dest_host = CONF.compute.migration_dest_host
        self._test_server_connectivity_cold_migration(
            source_host=source_host, dest_host=dest_host)

    @decorators.idempotent_id('1c13933e-79ae-11ee-b962-0242ac120002')
    @testtools.skipUnless(CONF.compute_feature_enabled.live_migration,
                          'Live migration is not available.')
    @testtools.skipUnless(CONF.compute.min_compute_nodes > 1,
                          'Less than 2 compute nodes, skipping multinode '
                          'tests.')
    @decorators.attr(type=['slow', 'multinode'])
    @utils.services('compute', 'network')
    def test_server_connectivity_live_migration(self):
        source_host = CONF.compute.migration_source_host
        dest_host = CONF.compute.migration_dest_host
        self._test_server_connectivity_live_migration(
            source_host=source_host, dest_host=dest_host, migration=True)

    @decorators.idempotent_id('2627789a-79ae-11ee-b962-0242ac120002')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration is not available.')
    @testtools.skipUnless(CONF.compute.min_compute_nodes > 1,
                          'Less than 2 compute nodes, skipping multinode '
                          'tests.')
    @decorators.attr(type=['slow', 'multinode'])
    @utils.services('compute', 'network')
    def test_server_connectivity_cold_migration_revert(self):
        source_host = CONF.compute.migration_source_host
        dest_host = CONF.compute.migration_dest_host
        self._test_server_connectivity_cold_migration_revert(
            source_host=source_host, dest_host=dest_host)
