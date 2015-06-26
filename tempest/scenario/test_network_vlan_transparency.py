# Copyright 2015 Cisco Systems
# All Rights Reserved.
#
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

from oslo_log import log as logging
from tempest import config
from tempest import exceptions
from tempest.scenario import test_network_multi_node

CONF = config.CONF
LOG = logging.getLogger(__name__)


class VlanNetwork():

    def __init__(self, vlan_id):
        self.vlan_id = vlan_id
        self.servers = {}
        self.ip_addrs = []

    def add_vm(self, id, interface, ip, client):
        self.servers[id] = {'interface': interface,
                            'ip': ip,
                            'client': client}

        self.ip_addrs.append(ip)

    def verify_inter_vm_connectivity(self, packet_count=10,
                                     packet_sizes=[56, 572]):
        """
        Cycles through and pings other VMs using the IP/VLAN interface.
        Verifies Pkt/Byte counts on the VLAN interface
        """
        if len(self.servers) < 2:
            return False

        for server in self.servers:
            vlan_interface = self.servers[server]['interface']
            linux_client = self.servers[server]['client']

            for packet_size in packet_sizes:
                pre_intf_stats = linux_client.interface_stats(
                    interface=vlan_interface)

                for ip in self.ip_addrs:
                    if ip is self.servers[server]['ip']:
                        continue

                    ping_result = linux_client.ping_host(ip,
                                                         count=packet_count,
                                                         size=packet_size,
                                                         interface=
                                                         vlan_interface,
                                                         interval=.2)

                    post_intf_stats = linux_client.interface_stats(
                        interface=vlan_interface)

                    tx_pkts = (post_intf_stats['tx']['pkts']
                               - pre_intf_stats['tx']['pkts'])

                    rx_pkts = (post_intf_stats['rx']['pkts']
                               - pre_intf_stats['rx']['pkts'])

                    rx_bytes = (post_intf_stats['rx']['bytes']
                                - pre_intf_stats['rx']['bytes'])

                    expected_bytes = packet_count * packet_size

                    if rx_pkts == 0 or rx_pkts != tx_pkts:
                        return False

                    if rx_bytes < expected_bytes:
                        return False

        return True


class TestNetworkVLANTransparency(test_network_multi_node.TestNetworkMultiNode):

    """
    VLAN Trunking or VLAN Transparency is a feature that allows a network
    to be configured with a tri-state boolean indicating if the network
    supports VLAN traffic originating from the VM.

    This test depends on the following:
        * The VLAN Transparency feature is configured on the stack.
        * The underlying network can support VLAN trunking/transparency.
        * The VMs used have the 802.1Q kernel module loaded or available
          to be loaded.
        * Tempest configuration variable
          CONF.network_feature_enabled.vlan_transparent is set to True

    The test inherits and builds on the test_network_multi_node test and
    depends on it to build a series of networks and places VMs on those
    networks.  Once the multi node base test completes this the following
    is done by this test:
        * Adds configuration to each VM for 802.1Q.
        * Configures the same VLAN on each VM attached to a network.
        * Verifies normal - non VLAN data path to each VM
        * Pings the VMs on each network using the VLAN interface.
        * Verifies traffic stats for the VLAN interface.
    """

    @classmethod
    def skip_checks(cls):
        super(TestNetworkVLANTransparency, cls).skip_checks()

    def setUp(self):
        super(TestNetworkVLANTransparency, self).setUp()
        if not CONF.network_feature_enabled.vlan_transparent:
            msg = ('The network feature vlan_transparent must be set to true'
                   ' for theses tests to run')
            raise exceptions.InvalidConfiguration(msg)

        for network in self.networks:
            self.assertTrue(network['vlan_transparent'],
                            "Networks are not enabled for VLAN Transparency")

        self.create_floating_ips()
        self.verify_vm_connectivity()
        self.setup_vm_vlans()

    def get_server_ip(self, server_id):
        if self.floating_ip_tuples is None:
            return None

        for i in range(0, len(self.floating_ip_tuples)):
            fip_tuple = self.floating_ip_tuples[i]
            target_ip, server = fip_tuple
            if server['id'] is server_id:
                return target_ip

        return None

    def setup_vm_vlans(self):
        """
        Determines if the VMs being used can actually create a VLAN interface
        and creates one.  Creates data structures used later to verify
        connectivity between VMs over VLANs.
        """
        self.vm_vlans = []
        vlan_id = 1000
        byte2 = 1
        byte3 = 1
        for network_id in self.network_vms:
            vlan_id += 1
            byte2 += 1
            if byte2 > 254:
                byte3 += 1
                byte2 = 1

            vlan_net = VlanNetwork(vlan_id)
            self.vm_vlans.append(vlan_net)
            server_num = 0
            for server in self.network_vms[network_id]:

                self.private_key = self.servers[server]['private_key']
                client_ip = self.get_server_ip(server)
                server_num += 1
                linux_client = self.get_remote_client(
                    server_or_ip=client_ip.floating_ip_address,
                    private_key=self.private_key)

                msg = "802.1q could not be enabled on VM kernel"
                if linux_client.is_dot1q_enabled() is False:
                    linux_client.load_dot1q()
                self.assertTrue(linux_client.is_dot1q_enabled(), msg)

                ip = "168.{0}.{1}.{2}".format(byte3, byte2, server_num)
                vlan_info = linux_client.config_dot1q(vlan_id=vlan_id,
                                                      ip_address=
                                                      str(ip + "/24"))
                vlan_re = re.compile(r"""
                                      ^\d+[:]\s*
                                      ([^@]+)
                                      [@]
                                      ([^:]+)[:]
                                      .*
                                      """,
                                     re.IGNORECASE | re.VERBOSE)

                vlan_id_re = re.compile(r"""
                                        ^\s+vlan\sprotocol\s802.1Q\sid\s+
                                        (\d+).*
                                        """,
                                        re.IGNORECASE | re.VERBOSE)

                for line in vlan_info.splitlines():
                    vlan_match = vlan_re.match(line)
                    if vlan_match:
                        vlan_interface = vlan_match.group(1)
                        parent_interface = vlan_match.group(2)
                        continue

                    vlan_match = vlan_id_re.match(line)
                    if vlan_match:
                        configured_vlan_id = vlan_match.group(1)

                if not configured_vlan_id:
                    msg = "VLAN not configure on server {0}".format(server)
                    raise exceptions.InvalidConfiguration(msg)

                self.assertEqual(int(vlan_id), int(configured_vlan_id))

                vlan_net.add_vm(id=server,
                                interface=vlan_interface,
                                ip=ip,
                                client=linux_client)

    def verify_vm_to_vm_vlan_connectivity(self):
        for vlan_net in self.vm_vlans:
            self.assertTrue(vlan_net.verify_inter_vm_connectivity())

    def test_network_vlan_transparency(self):
        self.verify_vm_to_vm_connectivity()
        self.verify_vm_to_vm_vlan_connectivity()
