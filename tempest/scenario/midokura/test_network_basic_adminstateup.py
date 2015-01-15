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

import os

from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario.midokura import manager
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)

# path should be described in tempest.conf
SCPATH = "/network_scenarios/"


class TestAdminStateUp(manager.AdvancedNetworkScenarioTest):
    """
        Scenario:
        TBA
    """

    def setUp(self):
        super(TestAdminStateUp, self).setUp()
        self.servers_and_keys = self.setup_topology(
            os.path.abspath(
                '{0}scenario_basic_adminstateup.yaml'.format(SCPATH)))

    def _check_connection(self, should_connect=True):
        ssh_login = CONF.compute.image_ssh_user
        floating_ip = self.servers_and_keys[0]['FIP']
        ip_address = floating_ip.floating_ip_address
        private_key = self.servers_and_keys[0]['keypair']['private_key']
        self.check_public_network_connectivity(
            ip_address, ssh_login, private_key, should_connect)

    def _check_vm_connectivity_router(self):
        tenant_routers = self._get_tenant_routers(tenant=self.tenant_id)
        for router in tenant_routers:
            self.network_client.update_router(
                router['id'], admin_state_up=False)
            LOG.info("router test")
            self._check_connection(False)
            self.network_client.update_router(
                router['id'], admin_state_up=True)

    def _check_vm_connectivity_net(self):
        for network in self.networks:
            LOG.info("network test")
            self.network_client.update_network(
                network['id'], admin_state_up=False)
            self._check_connection(False)
            self.network_client.update_network(
                network['id'], admin_state_up=True)

    def _check_vm_connectivity_port(self):
        LOG.info("port test")
        floating_ip = self.servers_and_keys[0]['FIP']
        port_id = floating_ip.get("port_id")
        self.network_client.update_port(
            port_id, admin_state_up=False)
        self._check_connection(False)
        self.network_client.update_port(
            port_id, admin_state_up=True)

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_adminstateup_router(self):
        LOG.info("Starting Router test")
        self._check_vm_connectivity_router()
        self._check_connection(True)
        LOG.info("End of Rotuer test")

    @test.skip_because(bug="1237807")
    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_adminstateup_network(self):
        LOG.info("Starting Network test")
        self._check_vm_connectivity_net()
        self._check_connection(True)
        LOG.info("End of Net test")

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_adminstateup_port(self):
        LOG.info("Starting Port test")
        self._check_vm_connectivity_port()
        self._check_connection(True)
        LOG.info("End of Port test")
