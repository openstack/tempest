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

import netaddr
import os

from tempest.openstack.common import log as logging
from tempest.scenario.midokura import manager
from tempest import test


LOG = logging.getLogger(__name__)

# path should be described in tempest.conf
SCPATH = "/network_scenarios/"
CIDR1 = "10.10.10.8/29"


class TestBasicMultisubnet(
        manager.AdvancedNetworkScenarioTest):
    """
        Scenario:
        TBA
    """

    def setUp(self):
        super(TestBasicMultisubnet, self).setUp()
        self.servers_and_keys = self.setup_topology(
            os.path.abspath(
                '{0}scenario_basic_multisubnet.yaml'.format(SCPATH)))

    def _check_vm_assignation(self):
        s1 = 0
        s2 = 0
        for pair in self.servers_and_keys:
            server = pair['server']
            network = server['addresses']
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
