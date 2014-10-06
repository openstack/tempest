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


class TestNetworkAdvancedSecurityGroups2Networks(
        manager.AdvancedNetworkScenarioTest):
    """
        Prerequisite:
            - two VMs A and B
            - in same tenant
            - in different subnets SnetA, SnetB
            - In the same and only SG Sg
            - Sg has no ingress or egress rules
            - VMs with net cat
    test1:
        Steps:
            1- send pint A to B
        Expecte results:
            Ping does NOT work
    test2:
        steps:
            1- add custom icmp rule in SG S,
                for ICMP type 8, code -1, for egress
            2- add custom icmp rule in SG S,
                for ICMP type 8, code -1, for ingress
            3- send ping A to B

        Expected results:
            ping does work
    """

    @classmethod
    def setUpClass(cls):
        super(TestNetworkAdvancedSecurityGroups2Networks, cls).setUpClass()
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkAdvancedSecurityGroups2Networks, self).setUp()
        self.servers_and_keys = self.setup_topology(
            os.path.abspath('{0}scenario_basic_2nets.yaml'.format(SCPATH)))

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_security_group_2nets(self):
        rulesets = [{
                    'direction': 'egress',
                    'protocol': 'icmp',
                    'port_range_min': 8,
                    'port_range_max': None, },
                    {
                    'direction': 'ingress',
                    'protocol': 'icmp',
                    'port_range_min': 8,
                    'port_range_max': None,
                    }]
        sg = self._get_security_group_by_name("sg")
        for rule in rulesets:
            self._create_security_group_rule(secgroup=sg, **rule)

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
        self._ping_through_gateway(nhops, vm2, should_succed=True)

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_security_group_2nets_negative(self):
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
        self._ping_through_gateway(nhops, vm2, should_succed=False)
