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


import itertools
import os

from tempest.openstack.common import log as logging
from tempest.scenario.midokura import manager
from tempest import test

LOG = logging.getLogger(__name__)
SCPATH = "/network_scenarios/"


class TestNetworkBasicInterVMConnectivity(manager.AdvancedNetworkScenarioTest):
    """
        Scenario:
        A launched VM should get an ip address
        and routing table entries from DHCP. And
        it should be able to metadata service.

        Pre-requisites:
        1 tenant
        1 network
        2 VMs

        Steps:
        1. create a network
        2. launch 2 VMs
        3. verify that 2 VMs can ping each other

        Expected results:
        ping works
    """
    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicInterVMConnectivity, cls).setUpClass()
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkBasicInterVMConnectivity, self).setUp()
        self.servers_and_keys = self.setup_topology(
                os.path.abspath('{0}scenario_basic_inter_vmconnectivity.yaml'.format(SCPATH)))
        
   
    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_inter_vmssh(self):
        ap_details = self.servers_and_keys[-1]
        ap = ap_details['server']
        networks = ap['addresses']
        hops=[(ap_details['FIP'].floating_ip_address, ap_details['keypair']['private_key'])]
        ip_pk = []
        #the access_point server should be the last one in the list
        for element in self.servers_and_keys[:-1]:
            # servers should only have 1 network
            server = element['server']
            name = server['addresses'].keys()[0]
            if any(i in networks.keys() for i in server['addresses'].keys()):
                remote_ip = server['addresses'][name][0]['addr']
                keypair = element['keypair']
                pk = keypair['private_key']
                ip_pk.append((remote_ip, pk))
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server['addresses'][name][0]['addr'])
                raise Exception("FAIL - No ip for this network : %s"
                            % server['addresses'][name])
        for pair in itertools.permutations(ip_pk):
            LOG.info("Checking ssh between %s %s"
                     % (pair[0][0], pair[1][0]))
            nhops = hops + [pair[0]]
            self._ssh_through_gateway(nhops, pair[1])
            LOG.info("Checking ping between %s %s"
                     % (pair[0][0], pair[1][0]))
            self._ping_through_gateway(hops, pair[1])
        LOG.info("test finished, tearing down now ....")
