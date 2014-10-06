
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
from tempest.scenario.midokura.midotools import helper
from tempest.scenario.midokura import manager
from tempest import test


LOG = logging.getLogger(__name__)
CIDR1 = "10.10.10.0/24"
# path should be described in tempest.conf
SCPATH = "/network_scenarios/"


class TestNetworkBasicDhcpLease(manager.AdvancedNetworkScenarioTest):
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
        self.servers_and_keys = \
            self.setup_topology(os.path.abspath('{0}scenario_basic_dhcp.yaml'.format(SCPATH)))

    def _check_routes(self, hops):
        LOG.info("Obtaining the routes")
        try:
            ssh_client = self.setup_tunnel(hops)
            route_out = ssh_client.exec_command("sudo /sbin/route -n")
            rtable = helper.Routetable.build_route_table(route_out)
            LOG.info(rtable)
            self.assertTrue(any([r.is_custom_route("172.20.0.0", "10.10.10.10")
                                 for r in rtable]))
        except Exception as inst:
            LOG.info(inst.args)
            raise

    def _check_dns(self, hops):
        LOG.info("Obtaining the routes")
        try:
            ssh_client = self.setup_tunnel(hops)
            dns = ssh_client.exec_command("cat /etc/resolv.conf | grep nameserver | "
                                          "awk '{print $2}'").replace("\n", "")
            LOG.info(dns)
            self.assertEqual(dns, "8.8.8.8")
        except Exception as inst:
            LOG.info(inst.args)
            raise

    def _do_dhcp_lease(self, hops):
        try:
            ssh_client = self.setup_tunnel(hops)
            pid = ssh_client.exec_command("ps fuax | grep udhcp | "
                                          "awk '{print $1}'").split("\n")[0]
            LOG.info(pid)
            out = ssh_client.exec_command("sudo kill -USR1 %s" % pid)
            LOG.info(out)
        except Exception as inst:
            LOG.info(inst.args)
            raise

    def _do_test(self, dns=True, routes=True):
        ap_details = self.servers_and_keys[-1]
        ap = ap_details['server']
        networks = ap['addresses']
        hops = [(ap_details['FIP'].floating_ip_address, ap_details['keypair']['private_key'])]
        # the last element is ignored since it is the gateway
        for element in self.servers_and_keys[:-1]:
            server = element['server']
            # servers should only have 1 network
            name = server['addresses'].keys()[0]
            if any(i in networks.keys() for i in server['addresses'].keys()):
                remote_ip = server['addresses'][name][0]['addr']
                keypair = element['keypair']
                pk = keypair['private_key']
                hops.append((remote_ip, pk))
                if routes:
                    LOG.info("Checking the routes before the lease")
                    self._check_routes(hops)
                if dns:
                    LOG.info("Checking the DNS before the lease")
                    self._check_dns(hops)
                self._do_dhcp_lease(hops)
                if routes:
                    LOG.info("Checking the routes after the lease")
                    self._check_routes(hops)
                if dns:
                    LOG.info("Checking the DNS after the lease")
                    self._check_dns(hops)
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server.networks[name][0])
                raise Exception("FAIL - No ip for this network : %s"
                                % server.networks)

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_dhcp_lease_full(self):
        self._do_test()
        LOG.info("test full finished, tearing down now ....")
    
    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_dhcp_lease_dns(self):
        self._do_test(dns=True, routes=False)
        LOG.info("test dns finished, tearing down now ....")

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_dhcp_lease_routes(self):
        self._do_test(dns=False, routes=True)
        LOG.info("test routes finished, tearing down now ....")
