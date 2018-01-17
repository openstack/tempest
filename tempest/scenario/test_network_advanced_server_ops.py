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

from tempest.common import utils
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators
from tempest.scenario import manager

CONF = config.CONF


class TestNetworkAdvancedServerOps(manager.NetworkScenarioTest):
    """Check VM connectivity after some advanced instance operations executed:

     * Stop/Start an instance
     * Reboot an instance
     * Rebuild an instance
     * Pause/Unpause an instance
     * Suspend/Resume an instance
     * Resize an instance
    """

    @classmethod
    def setup_clients(cls):
        super(TestNetworkAdvancedServerOps, cls).setup_clients()
        cls.admin_servers_client = cls.os_admin.servers_client

    @classmethod
    def skip_checks(cls):
        super(TestNetworkAdvancedServerOps, cls).skip_checks()
        if not (CONF.network.project_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            raise cls.skipException(msg)
        if not CONF.network_feature_enabled.floating_ips:
            raise cls.skipException("Floating ips are not available")

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(TestNetworkAdvancedServerOps, cls).setup_credentials()

    def _setup_server(self, keypair):
        security_groups = []
        if utils.is_extension_enabled('security-group', 'network'):
            security_group = self._create_security_group()
            security_groups = [{'name': security_group['name']}]
        network, _, _ = self.create_networks()
        server = self.create_server(
            networks=[{'uuid': network['id']}],
            key_name=keypair['name'],
            security_groups=security_groups)
        return server

    def _setup_network(self, server, keypair):
        public_network_id = CONF.network.public_network_id
        floating_ip = self.create_floating_ip(server, public_network_id)
        # Verify that we can indeed connect to the server before we mess with
        # it's state
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

        return floating_ip

    def _check_network_connectivity(self, server, keypair, floating_ip,
                                    should_connect=True):
        username = CONF.validation.image_ssh_user
        private_key = keypair['private_key']
        self.check_tenant_network_connectivity(
            server, username, private_key,
            should_connect=should_connect,
            servers_for_debug=[server])
        floating_ip_addr = floating_ip['floating_ip_address']
        # Check FloatingIP status before checking the connectivity
        self.check_floating_ip_status(floating_ip, 'ACTIVE')
        self.check_public_network_connectivity(floating_ip_addr, username,
                                               private_key, should_connect,
                                               servers=[server])

    def _wait_server_status_and_check_network_connectivity(self, server,
                                                           keypair,
                                                           floating_ip):
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')
        self._check_network_connectivity(server, keypair, floating_ip)

    def _get_host_for_server(self, server_id):
        body = self.admin_servers_client.show_server(server_id)['server']
        return body['OS-EXT-SRV-ATTR:host']

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
        self.servers_client.rebuild_server(server['id'],
                                           image_ref=image_ref_alt)
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

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
        resize_flavor = CONF.compute.flavor_ref_alt
        keypair = self.create_keypair()
        server = self._setup_server(keypair)
        floating_ip = self._setup_network(server, keypair)
        self.servers_client.resize_server(server['id'],
                                          flavor_ref=resize_flavor)
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'VERIFY_RESIZE')
        self.servers_client.confirm_resize_server(server['id'])
        server = self.servers_client.show_server(server['id'])['server']
        self.assertEqual(resize_flavor, server['flavor']['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @decorators.idempotent_id('a4858f6c-401e-4155-9a49-d5cd053d1a2f')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration is not available.')
    @testtools.skipUnless(CONF.compute.min_compute_nodes > 1,
                          'Less than 2 compute nodes, skipping multinode '
                          'tests.')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_server_connectivity_cold_migration(self):
        keypair = self.create_keypair()
        server = self._setup_server(keypair)
        floating_ip = self._setup_network(server, keypair)
        src_host = self._get_host_for_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

        self.admin_servers_client.migrate_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'VERIFY_RESIZE')
        self.servers_client.confirm_resize_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)
        dst_host = self._get_host_for_server(server['id'])

        self.assertNotEqual(src_host, dst_host)

    @decorators.idempotent_id('25b188d7-0183-4b1e-a11d-15840c8e2fd6')
    @testtools.skipUnless(CONF.compute_feature_enabled.cold_migration,
                          'Cold migration is not available.')
    @testtools.skipUnless(CONF.compute.min_compute_nodes > 1,
                          'Less than 2 compute nodes, skipping multinode '
                          'tests.')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_server_connectivity_cold_migration_revert(self):
        keypair = self.create_keypair()
        server = self._setup_server(keypair)
        floating_ip = self._setup_network(server, keypair)
        src_host = self._get_host_for_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

        self.admin_servers_client.migrate_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'VERIFY_RESIZE')
        self.servers_client.revert_resize_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)
        dst_host = self._get_host_for_server(server['id'])

        self.assertEqual(src_host, dst_host)
