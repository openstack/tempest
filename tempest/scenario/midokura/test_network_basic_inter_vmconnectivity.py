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
import threading
import time

from tempest.openstack.common import log as logging
from tempest.scenario.midokura.midotools import scenario
from tempest import test

LOG = logging.getLogger(__name__)
CIDR1 = "10.10.1.0/24"


class TestNetworkBasicInterVMConnectivity(scenario.TestScenario):
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
        self.security_group = \
            self._create_security_group_neutron(
                tenant_id=self.tenant_id)
        self._scenario_conf()
        self.custom_scenario(self.scenario)

    def _scenario_conf(self):
        serverB = {
            'floating_ip': False,
            'sg': None,
        }
        subnetA = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR1,
            "allocation_pools": None,
            "routers": None,
            "dns": [],
            "routes": [],
        }
        networkA = {
            'subnets': [subnetA],
            'servers': [serverB, serverB],
        }
        tenantA = {
            'networks': [networkA],
            'tenant_id': None,
            'type': 'default',
            'hasgateway': True,
            'MasterKey': True,
        }
        self.scenario = {
            'tenants': [tenantA],
        }

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_inter_vmssh(self):
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
            LOG.info("Checking ssh between %s %s"
                     % (pair[0][0], pair[1][0]))
            self._ssh_through_gateway(pair[0], pair[1])
            LOG.info("Checking ping between %s %s"
                     % (pair[0][0], pair[1][0]))
            self._ping_through_gateway(pair[0], pair[1])
        LOG.info("test finished, tearing down now ....")
        while threading.active_count() > 1:
                    time.sleep(0.1)