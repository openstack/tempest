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

import netaddr

from tempest.openstack.common import log as logging
from tempest.scenario.midokura.midotools import scenario
from tempest import test


LOG = logging.getLogger(__name__)
CIDR1 = "10.10.10.8/29"
CIDR2 = "10.10.1.8/29"


class TestBasicMultisubnet(scenario.TestScenario):

    @classmethod
    def setUpClass(cls):
        super(TestBasicMultisubnet, cls).setUpClass()
        cls.scenario = {}

    def setUp(self):
        super(TestBasicMultisubnet, self).setUp()
        self.security_group = \
            self._create_security_group_neutron(tenant_id=self.tenant_id)
        self._scenario_conf()
        self.custom_scenario(self.scenario)

    def _scenario_conf(self):
        serverA = {
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
        subnetB = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR2,
            "allocation_pools": None,
            "routers": None,
            "dns": [],
            "routes": [],
        }
        networkA = {
            'subnets': [subnetA, subnetB],
            'servers': [serverA, serverA, serverA, serverA, serverA]
        }
        tenantA = {
            'networks': [networkA],
            'tenant_id': None,
            'type': 'default',
            'hasgateway': False,
            'MasterKey': False,
        }
        self.scenario = {
            'tenants': [tenantA],
        }

    def _check_vm_assignation(self):
        s1 = 0
        s2 = 0
        for server in self.servers:
            network = server.addresses
            key, value = network.popitem()
            ip = value[0]['addr']
            if netaddr.IPAddress(ip) in netaddr.IPNetwork(CIDR1):
                s1 += 1
            else:
                s2 += 1
        return s1 == 4 or s2 == 4

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_multisubnet(self):
        self.assertTrue(self._check_vm_assignation())