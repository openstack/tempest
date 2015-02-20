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
from tempest.scenario.midokura import manager
from tempest import test

LOG = logging.getLogger(__name__)
SCPATH = "/network_scenarios/"


class TestNetworkBasicDhcpDisable(manager.AdvancedNetworkScenarioTest):
    """
        Scenario:
            Ability to disable DHCP
        Prerequisite:
            1 tenant
            1 network
            1 vm
        Steps:
            1) spawn the VM
            2) Disable the DHCP
            3) try to renew DHCP
        Expected result:
            can't renew the dhcp
    """

    def setUp(self):
        super(TestNetworkBasicDhcpDisable, self).setUp()
        self.servers_and_keys = self.setup_topology(
            os.path.abspath(
                '{0}scenario_basic_dhcp_disable.yaml'.format(SCPATH)))

    # this should be ported to "linux_client" class
    def _do_dhcp_lease(self, hops, timeout=0):
        try:
            ssh_client = self.setup_tunnel(hops)
            pid = ssh_client.exec_command("ps fuax | grep udhcp | "
                                          "awk '{print $1}'").split("\n")[0]
            LOG.info(pid)
            out = ssh_client.exec_command("sudo kill -USR1 %s" % pid, timeout)
            LOG.info(out)
        except Exception as inst:
            # should give a timeout
            if "Request timed out" == inst.message:
                LOG.debug(inst)
                pass
            else:
                raise

    def _get_ip(self, hops, timeout=0, shouldFail=False):
        try:
            ssh_client = self.setup_tunnel(hops)
            net_info = ssh_client.get_ip_list()
            LOG.debug(net_info)
            remote_ip, _ = hops[-1]
            pattern = re.compile(
                '[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}')
            list = pattern.findall(net_info)
            LOG.info(remote_ip)
            LOG.info(list)
            self.assertIn(remote_ip, list)
        except Exception:
            if shouldFail:
                pass
            else:
                raise

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_basic_dhcp_disable(self):
        ap_details = self.servers_and_keys[-1]
        ap = ap_details['server']
        networks = ap['addresses']
        hops = [(ap_details['FIP'].floating_ip_address,
                 ap_details['keypair']['private_key'])]
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
                LOG.info("Checking the IP before the lease")
                # get the ip
                self._get_ip(hops)
                net = self._get_network_by_name(name)[0]
                subn = net['subnets'][0]
                self._toggle_dhcp(subnet_id=subn)
                # should give timeout
                self._do_dhcp_lease(hops, 20)
                self._get_ip(hops, 10, True)
            else:
                LOG.info("FAIL - No ip connectivity to the server ip: %s"
                         % server.networks[name][0])
                raise Exception("FAIL - No ip for this network : %s"
                                % server.networks)
        LOG.info("test finished, tearing down now ....")
