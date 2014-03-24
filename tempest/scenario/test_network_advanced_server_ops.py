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

from tempest.common import debug
from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario import manager
from tempest.test import services

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestNetworkAdvancedServerOps(manager.NetworkScenarioTest):

    """
    This test case checks VM connectivity after some advanced
    instance operations executed:

     * Stop/Start an instance
     * Reboot an instance
     * Rebuild an instance
     * Pause/Unpause an instance
     * Suspend/Resume an instance
     * Resize an instance
    """

    @classmethod
    def setUpClass(cls):
        super(TestNetworkAdvancedServerOps, cls).setUpClass()
        cls.check_preconditions()
        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise cls.skipException(msg)

    def cleanup_wrapper(self, resource):
        self.cleanup_resource(resource, self.__class__.__name__)

    def setUp(self):
        super(TestNetworkAdvancedServerOps, self).setUp()
        key_name = data_utils.rand_name('keypair-smoke-')
        self.keypair = self.create_keypair(name=key_name)
        self.addCleanup(self.cleanup_wrapper, self.keypair)
        security_group =\
            self._create_security_group_neutron(tenant_id=self.tenant_id)
        self.addCleanup(self.cleanup_wrapper, security_group)
        network = self._create_network(self.tenant_id)
        self.addCleanup(self.cleanup_wrapper, network)
        router = self._get_router(self.tenant_id)
        self.addCleanup(self.cleanup_wrapper, router)
        subnet = self._create_subnet(network)
        self.addCleanup(self.cleanup_wrapper, subnet)
        subnet.add_to_router(router.id)
        public_network_id = CONF.network.public_network_id
        create_kwargs = {
            'nics': [
                {'net-id': network.id},
            ],
            'key_name': self.keypair.name,
            'security_groups': [security_group.name],
        }
        server_name = data_utils.rand_name('server-smoke-%d-')
        self.server = self.create_server(name=server_name,
                                         create_kwargs=create_kwargs)
        self.addCleanup(self.cleanup_wrapper, self.server)
        self.floating_ip = self._create_floating_ip(self.server,
                                                    public_network_id)
        self.addCleanup(self.cleanup_wrapper, self.floating_ip)

    def _check_tenant_network_connectivity(self, server,
                                           username,
                                           private_key,
                                           should_connect=True):
        if not CONF.network.tenant_networks_reachable:
            msg = 'Tenant networks not configured to be reachable.'
            LOG.info(msg)
            return
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        try:
            for net_name, ip_addresses in server.networks.iteritems():
                for ip_address in ip_addresses:
                    self._check_vm_connectivity(ip_address,
                                                username,
                                                private_key,
                                                should_connect=should_connect)
        except Exception:
            LOG.exception('Tenant network connectivity check failed')
            self._log_console_output(servers=[server])
            debug.log_ip_ns()
            raise

    def _check_public_network_connectivity(self, floating_ip,
                                           username,
                                           private_key,
                                           should_connect=True):
        # The target login is assumed to have been configured for
        # key-based authentication by cloud-init.
        try:
            self._check_vm_connectivity(floating_ip, username, private_key,
                                        should_connect=should_connect)
        except Exception:
            LOG.exception("Public network connectivity check failed")
            debug.log_ip_ns()
            raise

    def _check_network_connectivity(self, should_connect=True):
        username = CONF.compute.image_ssh_user
        private_key = self.keypair.private_key
        self._check_tenant_network_connectivity(self.server,
                                                username,
                                                private_key,
                                                should_connect=should_connect)
        floating_ip = self.floating_ip.floating_ip_address
        self._check_public_network_connectivity(floating_ip,
                                                username,
                                                private_key,
                                                should_connect=should_connect)

    def _wait_server_status_and_check_network_connectivity(self):
        self.status_timeout(self.compute_client.servers, self.server.id,
                            'ACTIVE')
        self._check_network_connectivity()

    @services('compute', 'network')
    def test_server_connectivity_stop_start(self):
        self.server.stop()
        self.status_timeout(self.compute_client.servers, self.server.id,
                            'SHUTOFF')
        self._check_network_connectivity(should_connect=False)
        self.server.start()
        self._wait_server_status_and_check_network_connectivity()

    @services('compute', 'network')
    def test_server_connectivity_reboot(self):
        self.server.reboot()
        self._wait_server_status_and_check_network_connectivity()

    @services('compute', 'network')
    def test_server_connectivity_rebuild(self):
        image_ref_alt = CONF.compute.image_ref_alt
        self.server.rebuild(image_ref_alt)
        self._wait_server_status_and_check_network_connectivity()

    @testtools.skipUnless(CONF.compute_feature_enabled.pause,
                          'Pause is not available.')
    @services('compute', 'network')
    def test_server_connectivity_pause_unpause(self):
        self.server.pause()
        self.status_timeout(self.compute_client.servers, self.server.id,
                            'PAUSED')
        self._check_network_connectivity(should_connect=False)
        self.server.unpause()
        self._wait_server_status_and_check_network_connectivity()

    @testtools.skipUnless(CONF.compute_feature_enabled.suspend,
                          'Suspend is not available.')
    @services('compute', 'network')
    def test_server_connectivity_suspend_resume(self):
        self.server.suspend()
        self.status_timeout(self.compute_client.servers, self.server.id,
                            'SUSPENDED')
        self._check_network_connectivity(should_connect=False)
        self.server.resume()
        self._wait_server_status_and_check_network_connectivity()

    @testtools.skipUnless(CONF.compute_feature_enabled.resize,
                          'Resize is not available.')
    @services('compute', 'network')
    def test_server_connectivity_resize(self):
        resize_flavor = CONF.compute.flavor_ref_alt
        if resize_flavor == CONF.compute.flavor_ref:
            msg = "Skipping test - flavor_ref and flavor_ref_alt are identical"
            raise self.skipException(msg)
        resize_flavor = CONF.compute.flavor_ref_alt
        self.server.resize(resize_flavor)
        self.status_timeout(self.compute_client.servers, self.server.id,
                            'VERIFY_RESIZE')
        self.server.confirm_resize()
        self._wait_server_status_and_check_network_connectivity()
