
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

import re
import os

from tempest.openstack.common import log as logging
from tempest.scenario.midokura.midotools import helper
from tempest.scenario.midokura import manager
from tempest import test


LOG = logging.getLogger(__name__)
# path should be described in tempest.conf
SCPATH = "/network_scenarios/"


class TestNetworkBasicVMConnectivity(manager.AdvancedNetworkScenarioTest):
    """
        Scenario:
        A launched VM should get an ip address and
        routing table entries from DHCP. And
        it should be able to metadata service.

        Pre-requisites:
        1 tenant
        1 network
        1 VM

        Steps:
        1. create a network
        2. launch a VM
        3. verify that the VM gets IP address
        4. verify that the VM gets default GW
           in the routing table
        5. verify that the VM gets a
           routing entry for metadata service via dhcp agent

        Expected results:
        vm should get an ip address (confirm by "ip addr" command)
        VM should get a defaut gw
        VM should get a route for 169.254.169.254 (on non-cirros )
    """

    def setUp(self):
        super(TestNetworkBasicVMConnectivity, self).setUp()
        self.servers_and_keys = self.setup_topology(
            os.path.abspath(
                '{0}scenario_basic_vmconnectivity.yaml'.format(SCPATH)))

    def _test_routes(self, hops):
        LOG.info("Trying to get the list of ips")
        try:
            ssh_client = self.setup_tunnel(hops)
            net_info = ssh_client.get_ip_list()
            LOG.debug(net_info)
            pattern = re.compile(
                '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
            ip_list = pattern.findall(net_info)
            LOG.debug(ip_list)
            remote_ip, _ = hops[-1]
            self.assertIn(remote_ip, ip_list)
            route_out = ssh_client.exec_command("sudo /sbin/route -n")
            self._check_default_gateway(route_out, remote_ip)
            LOG.info(route_out)
        except Exception as inst:
            LOG.info(inst.args)
            raise

    def _check_default_gateway(self, route_out, internal_ip):
        try:
            rtable = helper.Routetable.build_route_table(route_out)
            # TODO(QA): More extended route table tests
            LOG.debug(rtable)
            self.assertTrue(any([r.is_default_route() for r in rtable]))
        except Exception as inst:
            LOG.info(inst.args)
            raise

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_vmconnectivity(self):
        ap_details = self.servers_and_keys[-1]
        access_point = ap_details['server']
        networks = access_point['addresses']
        hops = [(ap_details['FIP'].floating_ip_address,
                ap_details['keypair']['private_key'])]
        # the access_point server should be the last one in the list
        for element in self.servers_and_keys[:-1]:
            if element['server']['name'].startswith('access_point'):
                continue
            server = element['server']
            name = server['addresses'].keys()[0]
            if any(i in networks.keys() for i in server['addresses'].keys()):
                remote_ip = server['addresses'][name][0]['addr']
                keypair = element['keypair']
                privatekey = keypair['private_key']
                hops.append((remote_ip, privatekey))
                self._test_routes(hops)
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server.networks[name][0])
                raise Exception("FAIL - No ip for this network : %s"
                                % server.networks)
        LOG.info("test finished, tearing down now ....")
