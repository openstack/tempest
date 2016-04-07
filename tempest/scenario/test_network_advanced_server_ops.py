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

from tempest.common.utils import data_utils
from tempest.common import waiters
from tempest import config
from tempest.scenario import manager
from tempest import test

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
    def skip_checks(cls):
        super(TestNetworkAdvancedServerOps, cls).skip_checks()
        if not (CONF.network.project_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(TestNetworkAdvancedServerOps, cls).setup_credentials()

    def _setup_network_and_servers(self):
        keypair = self.create_keypair()
        security_group = self._create_security_group()
        network, subnet, router = self.create_networks()
        public_network_id = CONF.network.public_network_id
        server_name = data_utils.rand_name('server-smoke')
        server = self.create_server(
            name=server_name,
            networks=[{'uuid': network.id}],
            key_name=keypair['name'],
            security_groups=[{'name': security_group['name']}],
            wait_until='ACTIVE')
        floating_ip = self.create_floating_ip(server, public_network_id)
        # Verify that we can indeed connect to the server before we mess with
        # it's state
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

        return server, keypair, floating_ip

    def _check_network_connectivity(self, server, keypair, floating_ip,
                                    should_connect=True):
        username = CONF.validation.image_ssh_user
        private_key = keypair['private_key']
        self._check_tenant_network_connectivity(
            server, username, private_key,
            should_connect=should_connect,
            servers_for_debug=[server])
        floating_ip_addr = floating_ip.floating_ip_address
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

    @test.idempotent_id('61f1aa9a-1573-410e-9054-afa557cab021')
    @test.stresstest(class_setup_per='process')
    @test.services('compute', 'network')
    def test_server_connectivity_stop_start(self):
        server, keypair, floating_ip = self._setup_network_and_servers()
        self.servers_client.stop_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'SHUTOFF')
        self._check_network_connectivity(server, keypair, floating_ip,
                                         should_connect=False)
        self.servers_client.start_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @test.idempotent_id('7b6860c2-afa3-4846-9522-adeb38dfbe08')
    @test.services('compute', 'network')
    def test_server_connectivity_reboot(self):
        server, keypair, floating_ip = self._setup_network_and_servers()
        self.servers_client.reboot_server(server['id'], type='SOFT')
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @test.idempotent_id('88a529c2-1daa-4c85-9aec-d541ba3eb699')
    @test.services('compute', 'network')
    def test_server_connectivity_rebuild(self):
        server, keypair, floating_ip = self._setup_network_and_servers()
        image_ref_alt = CONF.compute.image_ref_alt
        self.servers_client.rebuild_server(server['id'],
                                           image_ref=image_ref_alt)
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @test.idempotent_id('2b2642db-6568-4b35-b812-eceed3fa20ce')
    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @test.services('compute', 'network')
    def test_server_connectivity_pause_unpause(self):
        server, keypair, floating_ip = self._setup_network_and_servers()
        self.servers_client.pause_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'PAUSED')
        self._check_network_connectivity(server, keypair, floating_ip,
                                         should_connect=False)
        self.servers_client.unpause_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @test.idempotent_id('5cdf9499-541d-4923-804e-b9a60620a7f0')
    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @test.services('compute', 'network')
    def test_server_connectivity_suspend_resume(self):
        server, keypair, floating_ip = self._setup_network_and_servers()
        self.servers_client.suspend_server(server['id'])
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'SUSPENDED')
        self._check_network_connectivity(server, keypair, floating_ip,
                                         should_connect=False)
        self.servers_client.resume_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)

    @test.idempotent_id('719eb59d-2f42-4b66-b8b1-bb1254473967')
    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    @test.services('compute', 'network')
    def test_server_connectivity_resize(self):
        resize_flavor = CONF.compute.flavor_ref_alt
        if resize_flavor == CONF.compute.flavor_ref:
            msg = "Skipping test - flavor_ref and flavor_ref_alt are identical"
            raise self.skipException(msg)
        server, keypair, floating_ip = self._setup_network_and_servers()
        self.servers_client.resize_server(server['id'],
                                          flavor_ref=resize_flavor)
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'VERIFY_RESIZE')
        self.servers_client.confirm_resize_server(server['id'])
        self._wait_server_status_and_check_network_connectivity(
            server, keypair, floating_ip)
