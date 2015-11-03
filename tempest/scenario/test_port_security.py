# Copyright 2015 Cisco Systems, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_log import log as logging
import tempest_lib
from tempest_lib.common.utils import data_utils
import time

from tempest import config
from tempest.common import waiters
from tempest.scenario import manager
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestPortSecurityExtension(manager.NetworkScenarioTest):
    @test.idempotent_id('eaed2e09-7228-4e37-9286-7eeb0975ac01')
    @test.services('compute', 'network')
    def test_attach_mix_ports_to_vm(self):
        """
        Create network with IpV4 subnet
        Boot VM on this network
        Create multiple ports both with port_security_enabled=False
        and port_security_enabled=True
        Attach ports to VM
        """
        network = self._create_network(tenant_id=self.tenant_id)
        self._create_subnet(network=network)
        secure_port = self._create_port(network.id,
                                        port_security_enabled=True)
        insecure_port = self._create_port(network.id,
                                          port_security_enabled=False)
        self.assertEqual(False, insecure_port['port_security_enabled'])
        create_kwargs = {'networks': [{'uuid': network.id}]}
        server = self.create_server(create_kwargs=create_kwargs)

        self.interface_client.create_interface(server['id'],
                                               port_id=secure_port.id)
        self.addCleanup(self.interface_client.delete_interface, server['id'],
                        secure_port['id'])

        self.interface_client.create_interface(server=server['id'],
                                               port_id=insecure_port.id)

        self.addCleanup(self.interface_client.delete_interface, server['id'],
                        insecure_port['id'])
        port_list = self._list_ports(device_id=server['id'])
        self.assertEqual(3, len(port_list))

    def _create_server_on_network(self, network_id, ssh_key_name,
                                  security_group_name, server_name):
        server_kwargs = {'networks': [{'uuid': network_id}, ],
                         'key_name': ssh_key_name,
                         'security_groups': [{'name': security_group_name}], }
        server = self.create_server(name=server_name,
                                    create_kwargs=server_kwargs)
        waiters.wait_for_server_status(self.servers_client, server['id'],
                                       'ACTIVE')
        return server

    def _set_route(self, route_to, route_via, server_ip, private_key):
        ssh_client = self._ssh_to_server(server_ip, private_key)
        add_route_cmd = "sudo ip route add {destination} via {router}".format(
            destination=route_to,
            router=route_via
        )
        ssh_client.exec_command(add_route_cmd)

    def _prepare_server(self, server_name, network, key_pair_name, private_key,
                        security_group_name):
        server_data = self._create_server_on_network(
            network['id'], key_pair_name, security_group_name,
            data_utils.rand_name(server_name)
        )

        floating_ip = self.create_floating_ip(
            server_data,
            CONF.network.public_network_id
        )

        self._check_tenant_network_connectivity(
            server_data, CONF.compute.image_ssh_user,
            private_key, should_connect=True,
            servers_for_debug=[server_data])
        return server_data, floating_ip

    @test.idempotent_id('f98df1d2-363b-47f1-a608-f89eab459ecc')
    @test.services('compute', 'network')
    def test_severs_connectivity_two_networks(self):
        key_pair = self.create_keypair()
        private_key = key_pair['private_key']
        key_pair_name = key_pair['name']
        sec_group = self._create_security_group(namestart='port-security-test')
        sec_group_name = sec_group['name']
        networks = self._list_networks(tenant_id=self.tenant_id)
        self.assertNotEmpty(networks)
        src_net = networks[0]

        source_server, source_ip = self._prepare_server("source", src_net,
                                                        key_pair_name,
                                                        private_key,
                                                        sec_group_name
                                                        )

        router_server, router_ip = self._prepare_server("router", src_net,
                                                        key_pair_name,
                                                        private_key,
                                                        sec_group_name
                                                        )
        router_connection = self._ssh_to_server(router_ip.floating_ip_address,
                                                private_key,
                                                )
        result = router_connection.exec_command('whereis iptables')
        if result == 'iptables:\n':
            LOG.warning('Iptables  is not available on router, skipping')
            return
        destination_network = self._create_network(
            namestart='destination_network'
        )
        self._create_subnet(destination_network,
                            namestart='destination_subnet')

        through_port = self._create_port(destination_network['id'],
                                         namestart='through_port',
                                         security_groups=[sec_group['id']])

        self.interface_client.create_interface(server=router_server['id'],
                                               port_id=through_port['id']
                                               )

        interface_cfg = "sudo sh -c " \
                        "'cat >> /etc/network/interfaces' << EOF " \
                        "\nauto eth1\niface eth1 inet dhcp\nEOF"

        router_connection.exec_command(interface_cfg)
        router_connection.exec_command("sudo ifup eth1")

        destination_server = self._create_server_on_network(
            destination_network['id'], key_pair_name, sec_group_name,
            data_utils.rand_name("destination")
        )

        destination_port = self._list_ports(
            device_id=destination_server['id'])[0]

        destination_ip = destination_port['fixed_ips'][0]['ip_address']
        through_ip = through_port['fixed_ips'][0]['ip_address']

        # set route to destination server
        self._set_route(route_to=destination_ip,
                        route_via=router_ip.fixed_ip_address,
                        server_ip=source_ip.floating_ip_address,
                        private_key=private_key
                        )

        # set route to source server from destination server
        cmd = "sudo ip route add {to} via {via}".format(
            to=source_ip.fixed_ip_address, via=through_ip)

        router_connection.ssh_client.exec_command_on_remote_server(
            destination_ip, cmd)

        # setup forwarding on router server
        router_connection.exec_command("sudo sysctl net.ipv4.ip_forward=1")
        router_connection.exec_command("sudo iptables -t nat -A POSTROUTING "
                                       "--out-interface eth1 -j MASQUERADE ")
        router_connection.exec_command("sudo iptables -A FORWARD "
                                       "--in-interface eth0 -j ACCEPT")

        source_connection = self._ssh_to_server(source_ip.floating_ip_address,
                                                private_key,
                                                )
        self.assertRaises(tempest_lib.exceptions.SSHExecCommandFailed,
                          source_connection.ping_host, destination_ip)

        router_ports = self._list_ports(device_id=router_server['id'])
        for port in router_ports:
            self.network_client.update_port(port['id'],
                                            security_groups=[],
                                            port_security_enabled=False)
        time.sleep(10)
        source_connection.ping_host(destination_ip)
        ping_me = 'ping {} -c 1'.format(source_ip.fixed_ip_address)
        result = source_connection.ssh_client.exec_command_on_remote_server(
            destination_ip, ping_me
        )
        self.assertIn("1 packets transmitted, 1 received, 0% packet loss",
                      result)
