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
__author__ = 'Albert'
__email__ = "albert.vico@midokura.com"

import itertools

from tempest.openstack.common import log as logging
from tempest.scenario.midokura.midotools import scenario
from tempest import test

LOG = logging.getLogger(__name__)
CIDR1 = "10.10.10.0/24"
CIDR2 = "10.10.2.0/24"


class TestNetworkBasicSecurityGroups(scenario.TestScenario):
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
            verify that vm3 cannot be talk to vm1 or vm2
        Expected result:
            vm3 can ping to vm1 and vm2 but not vice versa
    """

    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicSecurityGroups, cls).setUpClass()
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkBasicSecurityGroups, self).setUp()
        self.security_group = \
            self._create_security_group_neutron(tenant_id=self.tenant_id)
        self._scenario_conf()
        self.custom_scenario(self.scenario)

    def _scenario_conf(self):
        vm1 = {
            'floating_ip': False,
            'sg': ["default"],
        }
        vm2 = {
            'floating_ip': False,
            'sg': ["default"],
        }
        routerA = {
            "public": False,
            "name": "router_1"
        }
        subnetA = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR1,
            "allocation_pools": None,
            "routers": [routerA],
            "dns": [],
            "routes": [],
        }
        subnetB = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR2,
            "allocation_pools": None,
            "routers": [routerA],
            "dns": [],
            "routes": [],
        }
        networkA = {
            'subnets': [subnetA],
            'servers': [vm1],
        }
        networkB = {
            'subnets': [subnetB],
            'servers': [vm2],
        }
        tenantA = {
            'networks': [networkA, networkB],
            'tenant_id': None,
            'type': 'default',
            'hasgateway': True,
            'MasterKey': True,
        }
        self.scenario = {
            'tenants': [tenantA],
        }

    def _create_vm3_and_sg1(self):
        # creates the vm3 and assigns it sc "sg1"
        net = self.networks[0]
        sg = self._create_custom_security_group("sg1")
        server = self._create_server("vm3", net, security_groups=[sg.name])['server']
        return server

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_security_group(self):
        # we get the access point server
        ap_details = self.access_point.keys()[0]
        networks = ap_details.networks
        ip_pk = []
        for server in self.servers:
            # servers should only have 1 network
            name = server.networks.keys()[0]
            if any(i in networks.keys() for i in server.networks.keys()):
                remote_ip = server.networks[name][0]
                pk = self.servers[server].private_key
                ip_pk.append((remote_ip, pk))
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server.networks[name][0])
                raise Exception("FAIL - No ip for this network : %s"
                            % server.networks)
        for pair in itertools.permutations(ip_pk):
            self._ssh_through_gateway(pair[0], pair[1])
            LOG.info("Checking ping between %s %s"
                     % (pair[0][0], pair[1][0]))
            self._ping_through_gateway(pair[0], pair[1])

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_multi_security_group(self):
        vm3  = self._create_vm3_and_sg1()
        # we get the access point server
        ap_details = self.access_point.keys()[0]
        networks = ap_details.networks
        for server in self.servers:
            name = server.networks.keys()[0]
            if any(i in networks.keys() for i in server.networks.keys()):
                remote_ip = server.networks[name][0]
                pk = self.servers[server].private_key
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server.networks[name][0])
                raise Exception("FAIL - No ip for this network : %s"
                            % server.networks)
            self._ping_through_gateway((remote_ip, pk), vm3.networks.values()[0], should_fail=True)






