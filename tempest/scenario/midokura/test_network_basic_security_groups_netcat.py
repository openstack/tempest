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



from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario.midokura.midotools import scenario
from tempest import test


LOG = logging.getLogger(__name__)
CIDR1 = "10.10.10.0/24"
CONF = config.CONF

class TestNetworkBasicSecurityGroupsNetcat(scenario.TestScenario):
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

    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicSecurityGroupsNetcat, cls).setUpClass()
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkBasicSecurityGroupsNetcat, self).setUp()
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
            'servers': [vm1, vm2],
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

    def _netcat_test(self, ip_server, ssh_server, ssh_client):
        ssh_server.exec_command("nc -l -p 50000 > test.txt &")
        ssh_client.exec_command("echo '123' > send.txt")
        ssh_client.exec_command("nc %s 50000 < send.txt" % ip_server)
        result = ssh_server.exec_command("cat test.txt")
        return result

    def _test_netcat(self, source, destination):
        ssh_client = self.setup_tunnel([destination])
        ssh_server = self.setup_tunnel([source])
        result = self._netcat_test(source[0], ssh_server, ssh_client)
        LOG.info(result)
        self.assertEqual("123\n", result)

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_security_group(self):
        # we get the access point server
        #import ipdb; ipdb.set_trace()
        vm1_server = self.servers.items()[0][0]
        vm2_server = self.servers.items()[1][0]
        vm1_pk = self.servers[vm1_server].private_key
        vm2_pk = self.servers[vm2_server].private_key
        vm1 = (vm1_server.networks.values()[0][0], vm1_pk)
        vm2 = (vm2_server.networks.values()[0][0], vm2_pk)
        self._test_netcat(vm1, vm2)