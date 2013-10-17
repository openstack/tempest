
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

from tempest.openstack.common import log as logging
from tempest.scenario.midokura.midotools import helper
from tempest.scenario.midokura.midotools import scenario
from tempest import test


LOG = logging.getLogger(__name__)
CIDR1 = "10.10.10.0/24"


class TestNetworkBasicDhcpLease(scenario.TestScenario):
    """
        Scenario:
            a VM obtains a DHCP lease with host routes

        Pre-requisites:
            1 tenant
            1 network
            1 VM

        Steps:
            1) Spawn a VM.
            2)Get a dhcp lease.
            3) configure the subnetwork CDIR:10.10.10.0/24 with a
            DNS: 8.8.8.8 and a route: Destination 172.20.0.0/24 :
            Next hop 10.10.10.10
            3) Verify the routes and DNS entry (on cirros,
            capture the traffic from tap, since it doesn't allow
             getting routes in DHCP)

        Expected results:
            Packets with the routes and the dns entry should reach the vm.
    """

    @classmethod
    def setUpClass(cls):
        super(TestNetworkBasicDhcpLease, cls).setUpClass()
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkBasicDhcpLease, self).setUp()
        self.security_group = \
            self._create_security_group_neutron(tenant_id=self.tenant_id)
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
            "dns": ["8.8.8.8"],
            "routes": [
                        {
                            "nexthop": "10.10.10.10",
                            "destination": "172.20.0.0/24"
                        }],
            "routers": None,
        }
        networkA = {
            'subnets': [subnetA],
            'servers': [serverB],
        }
        tenantA = {
            'networks': [networkA],
            'tenant_id': None,
            'type': 'default',
            'hasgateway': True,
            'MasterKey': False,
        }
        self.scenario = {
            'tenants': [tenantA],
        }

    def _check_routes(self, remote_ip, pk):
        LOG.info("Obtaining the routes")
        try:
            ssh_client = self.setup_tunnel([(remote_ip, pk)])
            route_out = ssh_client.exec_command("sudo /sbin/route -n")
            rtable = helper.Routetable.build_route_table(route_out)
            LOG.info(rtable)
            self.assertTrue(any([r.is_custom_route("172.20.0.0", "10.10.10.10")
                                 for r in rtable]))
        except Exception as inst:
            LOG.info(inst.args)
            raise

    def _check_dns(self, remote_ip, pk):
        LOG.info("Obtaining the routes")
        try:
            ssh_client = self.setup_tunnel([(remote_ip, pk)])
            dns = ssh_client.exec_command("cat /etc/resolv.conf | grep nameserver | "
                                          "awk '{print $2}'").replace("\n", "")
            LOG.info(dns)
            self.assertEqual(dns, "8.8.8.8")
        except Exception as inst:
            LOG.info(inst.args)
            raise

    def _do_dhcp_lease(self, remote_ip,pk):
        try:
            ssh_client = self.setup_tunnel([(remote_ip, pk)])
            pid = ssh_client.exec_command("ps fuax | grep udhcp | "
                                          "awk '{print $1}'").split("\n")[0]
            LOG.info(pid)
            out = ssh_client.exec_command("sudo kill -USR1 %s" % pid)
            LOG.info(out)
        except Exception as inst:
            LOG.info(inst.args)
            raise

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_dhcp_lease_full(self):
        ap_details = self.access_point.keys()[0]
        networks = ap_details.networks
        for server in self.servers:
            # servers should only have 1 network
            name = server.networks.keys()[0]
            if any(i in networks.keys() for i in server.networks.keys()):
                remote_ip = server.networks[name][0]
                pk = self.servers[server].private_key

                LOG.info("Checking the routes and DNS before the lease")
                self._check_routes(remote_ip, pk)
                self._check_dns(remote_ip, pk)
                self._do_dhcp_lease(remote_ip, pk)
                LOG.info("Checking the routes and DNS after the lease")
                self._check_routes(remote_ip, pk)
                self._check_dns(remote_ip, pk)
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server.networks[name][0])
                raise Exception("FAIL - No ip for this network : %s"
                                % server.networks)
        LOG.info("test finished, tearing down now ....")

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_dhcp_lease_dns(self):
        ap_details = self.access_point.keys()[0]
        networks = ap_details.networks
        for server in self.servers:
            # servers should only have 1 network
            name = server.networks.keys()[0]
            if any(i in networks.keys() for i in server.networks.keys()):
                remote_ip = server.networks[name][0]
                pk = self.servers[server].private_key
                LOG.info("Checking the DNS before the lease")
                self._check_dns(remote_ip, pk)
                self._do_dhcp_lease(remote_ip, pk)
                LOG.info("Checking the DNS after the lease")
                self._check_dns(remote_ip, pk)
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server.networks[name][0])
                raise Exception("FAIL - No ip for this network : %s"
                                % server.networks)
        LOG.info("test finished, tearing down now ....")

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_dhcp_lease_routes(self):
        ap_details = self.access_point.keys()[0]
        networks = ap_details.networks
        for server in self.servers:
            # servers should only have 1 network
            name = server.networks.keys()[0]
            if any(i in networks.keys() for i in server.networks.keys()):
                remote_ip = server.networks[name][0]
                pk = self.servers[server].private_key
                LOG.info("Checking the DNS before the lease")
                self._check_routes(remote_ip, pk)
                self._do_dhcp_lease(remote_ip, pk)
                LOG.info("Checking the DNS after the lease")
                self._check_routes(remote_ip, pk)
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server.networks[name][0])
                raise Exception("FAIL - No ip for this network : %s"
                                % server.networks)
        LOG.info("test finished, tearing down now ....")
