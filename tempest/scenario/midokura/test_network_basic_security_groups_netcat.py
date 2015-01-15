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


LOG = logging.getLogger(__name__)
CONF = config.CONF
SCPATH = "/network_scenarios/"


class TestNetworkBasicSecurityGroupsNetcat(
        manager.AdvancedNetworkScenarioTest):
    """
        Scenario:
            check default SG behavior for TCP
        Prerequisite:
            two VMs A and B
            in same tenant,
            in same subnet
            with default SG (the one that comes with OS)
            VMs with net cat
        Steps:
            1- in B run netcat server,
                listening on TCP a system port 50000
            2- in A run netcat client,
                connect to B with TCP.
            3- type "123" in A
        Expected result:
            check B receives "123"
    """

    def setUp(self):
        super(TestNetworkBasicSecurityGroupsNetcat, self).setUp()
        self.servers_and_keys = self.setup_topology(
            os.path.abspath('{0}scenario_basic_netcat.yaml'.format(SCPATH)))

    def _netcat_test(self, ip_server, ssh_server, ssh_client):
        ssh_server.exec_command("nc -l -p 50000 > test.txt &")
        ssh_client.exec_command("echo '123' > send.txt")
        ssh_client.exec_command("nc %s 50000 < send.txt &" % ip_server, 20)
        result = ssh_server.exec_command("cat test.txt")
        return result

    def _netcat_test_udp(self, ip_server, ssh_server, ssh_client):
        ssh_server.exec_command("nc -lu -p 50000 > test.txt &")
        ssh_client.exec_command("echo '123' > send.txt")
        ssh_client.exec_command("nc -u %s 50000 < send.txt &" % ip_server, 20)
        result = ssh_server.exec_command("cat test.txt")
        return result

    def _test_netcat(self, source, destination, udp=False):
        ap_details = self.servers_and_keys[-1]
        hop = [(ap_details['FIP'].floating_ip_address,
                ap_details['keypair']['private_key'])]
        d_hops = hop + [destination]
        s_hops = hop + [source]
        ssh_client = self.setup_tunnel(d_hops)
        ssh_server = self.setup_tunnel(s_hops)
        if udp:
            result = self._netcat_test_udp(source[0], ssh_server, ssh_client)
        else:
            result = self._netcat_test(source[0], ssh_server, ssh_client)
        LOG.info(result)
        self.assertEqual("123\n", result)

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_netcat_udp(self):
        # we get the access point server
        vm1_server = self.servers_and_keys[0]['server']
        vm2_server = self.servers_and_keys[1]['server']
        vm1_pk = self.servers_and_keys[0]['keypair']['private_key']
        vm2_pk = self.servers_and_keys[0]['keypair']['private_key']
        vm1 = (vm1_server['addresses'].values()[0][0]['addr'], vm1_pk)
        vm2 = (vm2_server['addresses'].values()[0][0]['addr'], vm2_pk)
        self._test_netcat(vm1, vm2, udp=True)

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_netcat(self):
        # we get the access point server
        vm1_server = self.servers_and_keys[0]['server']
        vm2_server = self.servers_and_keys[1]['server']
        vm1_pk = self.servers_and_keys[0]['keypair']['private_key']
        vm2_pk = self.servers_and_keys[0]['keypair']['private_key']
        vm1 = (vm1_server['addresses'].values()[0][0]['addr'], vm1_pk)
        vm2 = (vm2_server['addresses'].values()[0][0]['addr'], vm2_pk)
        self._test_netcat(vm1, vm2)

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_default_security_group(self):
        # we get the access point server
        ap_details = self.servers_and_keys[-1]
        hop = [(ap_details['FIP'].floating_ip_address,
                ap_details['keypair']['private_key'])]
        vm1_server = self.servers_and_keys[0]['server']
        vm2_server = self.servers_and_keys[1]['server']
        vm1_pk = self.servers_and_keys[0]['keypair']['private_key']
        vm2_pk = self.servers_and_keys[0]['keypair']['private_key']
        vm1 = (vm1_server['addresses'].values()[0][0]['addr'], vm1_pk)
        vm2 = (vm2_server['addresses'].values()[0][0]['addr'], vm2_pk)
        hop.append(vm1)
        self._ping_through_gateway(hop, vm2)
