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

from tempest.openstack.common import log as logging
from tempest.scenario.midokura import manager
from tempest import test

LOG = logging.getLogger(__name__)
SCPATH = "/network_scenarios/"


class TestNetworkAdvancedInterVMConnectivity(
        manager.AdvancedNetworkScenarioTest):
    """
        Scenario:
        VMs with "default" security groups can
        on different networks connected by a common
        router should be able to talk to each other

        Pre-requisites:
        1 tenant
        2 network
        1 router
        2 VMs

        Steps:
        1. create two networks with subnets
        2. create a router
        3. connect a router with both subnets
        4.  launch one VM for each network
        5. verify that VMs can ping and ssh each other

        Expected results:
        Ping should work.
        SSH should work.
    """

    def setUp(self):
        super(TestNetworkAdvancedInterVMConnectivity, self).setUp()
        self.servers_and_keys = self.setup_topology(
            os.path.abspath('{0}scenario_advanced_inter_vmcon.yaml'.format(
                            SCPATH)))

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_advanced_inter_vmssh(self):
        ap_details = self.servers_and_keys[-1]
        hops = [(ap_details['FIP'].floating_ip_address,
                 ap_details['keypair']['private_key'])]
        vm1_server = self.servers_and_keys[0]['server']
        vm2_server = self.servers_and_keys[1]['server']
        vm1_pk = self.servers_and_keys[0]['keypair']['private_key']
        vm2_pk = self.servers_and_keys[0]['keypair']['private_key']
        vm1 = (vm1_server['addresses'].values()[0][0]['addr'], vm1_pk)
        vm2 = (vm2_server['addresses'].values()[0][0]['addr'], vm2_pk)
        nhops = hops + [vm1]
        LOG.info("testing ssh between {0} and {1}".format(
                 vm1[0], vm2[0]))
        self._ssh_through_gateway(nhops, vm2)
        LOG.info("testing ping between {0} and {1}".format(
                 vm1[0], vm2[0]))
        self._ping_through_gateway(nhops, vm2)
        LOG.info("test finished, tearing down now ....")
