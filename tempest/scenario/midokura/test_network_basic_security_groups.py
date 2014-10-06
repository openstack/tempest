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


class TestNetworkBasicSecurityGroups(manager.AdvancedNetworkScenarioTest):
    """
        Scenario:
            launch 2 VMs in the "default" security group
            they should be able to communicate over icmp, tcp, udp
        Prerequisite:
            1 tenant
            2 networks net-a and net-b
            1 router
            1 extra SG "sg1" is created with default rules
            2 VMs one on each network
        Steps:
            launch vm1 on net-a with the "default" SG
            launch vm2 on net-b with the "default" SG
            launch vm3 on net-a with the "sg1" SG
            verify that vm1 can ping to vm2
            verify that vm1 can ssh into vm2
            verify that vm1 can talk to vm2 over udp
            verify that vm3 cannot talk to vm1 or vm2
        Expected result:
            vm3 can ping to vm1 and vm2 but not vice versa
    """

    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicSecurityGroups, cls).setUpClass()
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkBasicSecurityGroups, self).setUp()
        self.servers_and_keys = self.setup_topology(
            os.path.abspath('{0}scenario_basic_security_groups.yaml'.format(SCPATH)))
        
    def _create_vm3_and_sg1(self):
        # creates the vm3 and assigns it sc "sg1"
        net = self._get_network_by_name('netA')
        sg = self._create_empty_security_group(tenant_id=self.tenant_id,
                namestart="sg1")
        server = self._create_server(name="vm3", networks=net,
                 security_groups=[sg], has_FIP=False)['server']
        return server

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_security_group(self):
        # we get the access point server
        ap_details = self.servers_and_keys[-1]
        ap = ap_details['server']
        networks = ap['addresses']
        hops=[(ap_details['FIP'].floating_ip_address,
             ap_details['keypair']['private_key'])]
        ip_pk = []
        for element in self.servers_and_keys[:-1]:
            # servers should only have 1 network
            server = element['server']
            name = server['addresses'].keys()[0]
            if any(i in networks.keys() for i in server['addresses'].keys()):
                remote_ip = server['addresses'][name][0]['addr']
                pk = element['keypair']['private_key']
                ip_pk.append((remote_ip, pk))
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server['addresses'][name][0]['addr'])
                raise Exception("FAIL - No ip for this network : %s"
                            % server['addresses'][name])
        for pair in itertools.permutations(ip_pk):
            nhops = hops + [pair[0]]
            self._ssh_through_gateway(nhops, pair[1])
            LOG.info("Checking ping between %s %s"
                     % (pair[0][0], pair[1][0]))
            self._ping_through_gateway(hops, pair[1])

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_multi_security_group(self):
        vm3  = self._create_vm3_and_sg1()
        # we get the access point server
        ap_details = self.servers_and_keys[-1]
        ap = ap_details['server']
        networks = ap['addresses']
        hops=[(ap_details['FIP'].floating_ip_address,
             ap_details['keypair']['private_key'])]
        server = self.servers_and_keys[0]['server']
        name = server['addresses'].keys()[0]
        if any(i in networks.keys() for i in server['addresses'].keys()):
            remote_ip = server['addresses'][name][0]['addr']
            pk = self.servers_and_keys[0]['keypair']['private_key']
            nhops = hops + [(remote_ip, pk)]
        else:
            LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server['addresse'][name][0]['addr'])
            raise Exception("FAIL - No ip for this network : %s"
                            % server['addresses'][name])
        self._ping_through_gateway(nhops,
                    vm3['addresses'].values()[0], 
                    should_succed=False)
