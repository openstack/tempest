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
from tempest_lib import exceptions
from tempest.common import waiters
from tempest import config
from tempest.scenario import manager
from tempest import test
import time

CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestArpPoisoning(manager.NetworkScenarioTest):
    ip_to_ping = '8.8.8.8'
    poison_arp = '''
from struct import pack, unpack
import socket

def poison_arp(victim_ip, router_ip, iface="eth0"):
    arp_reply = pack("!H", 0x0002)
    broadcast_mac = pack("!6B", *(0xFF,) * 6)
    proto_arp = pack("!H", 0x0806)
    proto_ip = pack("!HHBB", 0x0001, 0x0800, 0x0006, 0x0004)
    sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.SOCK_RAW)
    sock.bind((iface, socket.SOCK_RAW))
    attacker_mac = sock.getsockname()[4]

    sender_ip = pack("!4B", *[int(x) for x in router_ip.split(".")])
    victim_ip = pack("!4B", *[int(x) for x in victim_ip.split(".")])
    request = [broadcast_mac, attacker_mac, proto_arp,
               proto_ip, arp_reply, attacker_mac, sender_ip,
               attacker_mac, victim_ip]
    request = "".join(request)
    while True:
        sock.send(request)
poison_arp("{victim_ip}", "{router_ip}")
'''

    @classmethod
    def resource_setup(cls):
        super(TestArpPoisoning, cls).resource_setup()
        compute_nodes = cls.admin_manager.hosts_client.list_hosts()['hosts']
        cls.compute_nodes = map(lambda x: x.get('host_name'),
                                filter(lambda y: y.get('service') == 'compute',
                                       compute_nodes))
        cls.servers = {}
        cls.aggregates = []

    def _boot_server(self, network, name, avail_zone=None):
        server_kwargs = {
            'networks': [{'uuid': network['id']}],
            'key_name': self.key_pair['name'],
            'security_groups': [{'name': self.sec_group['name']}],
            'availability_zone': avail_zone or 'nova'

        }
        server = self.create_server(name=name, create_kwargs=server_kwargs)
        self.servers[name] = server
        floating_ip = self.create_floating_ip(server,
                                              CONF.network.public_network_id)
        return floating_ip

    @staticmethod
    def upload_and_run_script(ssh_connection, script, script_name):
        ssh_connection.exec_command("touch ./{}.py".format(script_name))
        ssh_connection.exec_command("echo '{}' "
                                    "> ./{}.py".format(script, script_name))
        ssh_connection.exec_command("sudo nohup python "
                                    "./{}.py > ./{}.log 2>&1 &"
                                    .format(script_name, script_name))

    def _get_tenant_network(self):
        networks = self._list_networks(tenant_id=self.tenant_id)
        self.assertNotEmpty(networks)
        return networks[0]

    def _boot_servers(self, network=None, multi_compute=False):
        self.key_pair = self.create_keypair()
        self.sec_group = self._create_security_group()
        if not network:
            network = self._get_tenant_network()
        attacker_avail_zone = target_avail_zone = 'nova'
        if multi_compute:
            attacker_avail_zone = self.aggregates[0]
            target_avail_zone = self.aggregates[1]
        target_vm_ip = self._boot_server(network, 'target_vm',
                                         target_avail_zone)
        attacker_vm_ip = self._boot_server(network, 'attacker_vm',
                                           attacker_avail_zone)
        return attacker_vm_ip, target_vm_ip

    def run_arp_poisoning_test(self, attacker_vm_ip, target_vm_ip,
                               network=None):
        network = network or self._get_tenant_network()
        target_vm_connection = self._ssh_to_server(
            target_vm_ip.floating_ip_address, self.key_pair['private_key']
        )
        attacker_vm_connection = self._ssh_to_server(
            attacker_vm_ip.floating_ip_address, self.key_pair['private_key']
        )
        try:
            python_path = attacker_vm_connection.exec_command("which python")
            if not python_path:
                LOG.warning("No python is available, skipping test")
                return
        except exceptions.SSHExecCommandFailed:
            LOG.warning("No python is available, skipping test")
            return
        subnets = self._list_subnets(tenant_id=self.tenant_id,
                                     network=network)
        gateway_ip = subnets[0]['gateway_ip']
        attacker_vm_connection.exec_command(
            "echo '1' | sudo tee /proc/sys/net/ipv4/ip_forward"
        )

        target_vm_connection.exec_command("ping {} >/dev/null 2>&1 &"
                                          .format(TestArpPoisoning.ip_to_ping))
        time.sleep(10)
        script = TestArpPoisoning.poison_arp.format(
            victim_ip=target_vm_ip.fixed_ip_address,
            router_ip=gateway_ip)

        TestArpPoisoning.upload_and_run_script(attacker_vm_connection, script,
                                               'poison_arp')

        # make sure that arp packages is sent to target
        attacker_vm_connection.exec_command(
            "sudo nohup tcpdump arp and src {} and dst {} "
            " -c 1 -w ./poison.pcap > /dev/null 2>&1 &".format(
                gateway_ip, target_vm_ip.fixed_ip_address
            )
        )

        time.sleep(30)
        arp_pcap = attacker_vm_connection.exec_command(
            "du ./poison.pcap | awk '{print $1}'"
        )
        self.assertNotEqual(0, int(arp_pcap))

        attacker_vm_connection.exec_command(
            "sudo nohup tcpdump icmp and src {} "
            "or icmp and dst {} -c 1 -w ./captured.pcap"
            " > /dev/null 2>&1 &".format(target_vm_ip.fixed_ip_address,
                                         target_vm_ip.fixed_ip_address))

        # wait till arp poisoning take effect
        time.sleep(30)
        captured = attacker_vm_connection.exec_command(
            "du  ./captured.pcap | awk '{print $1}'"
        )
        self.assertEqual(0, int(captured))

    @test.idempotent_id('778904f3-9ee6-44c0-a946-bc103519da80')
    @test.services('compute', 'network')
    def test_arp_poisoning_single_compute_node(self):
        attacker_vm_ip, target_vm_ip = self._boot_servers()
        self.run_arp_poisoning_test(attacker_vm_ip, target_vm_ip)

    @test.idempotent_id('e0eb97ef-1068-49ee-87b8-f398facddef6')
    @test.services('compute', 'network')
    def test_arp_poisoning_single_compute_node_shared_network(self):
        shared_network = self._create_network(
            networks_client=self.admin_manager.networks_client,
            tenant_id=self.admin_manager.network_client.tenant_id,
            shared=True
        )
        subnet = self._create_subnet(shared_network,
                                     client=self.admin_manager.network_client)
        router = self._list_routers(tenant_id=self.tenant_id)[0]
        self.admin_manager.network_client.add_router_interface_with_subnet_id(
            router['id'], subnet['id']
        )
        self.addCleanup(
            self.admin_manager.network_client
                .remove_router_interface_with_subnet_id, router['id'],
            subnet['id'])
        attacker_vm, target_vm = \
            self._boot_servers(network=shared_network)
        self.run_arp_poisoning_test(attacker_vm, target_vm, shared_network)

    @test.idempotent_id('e1f8a5fc-befd-4ef8-9de7-58ee7a8e3090')
    @test.services('compute', 'network')
    def test_restart_nova_service_single_node(self):
        attacker_vm_ip, target_vm_ip = self._boot_servers()
        self.run_arp_poisoning_test(attacker_vm_ip, target_vm_ip)
        compute_to_disable = self.compute_nodes[-1]
        self.admin_manager.services_client.disable_service(
            host=compute_to_disable, binary='nova-compute')
        time.sleep(10)
        self.admin_manager.services_client.enable_service(
            host=compute_to_disable, binary='nova-compute')
        time.sleep(10)
        self.run_arp_poisoning_test(attacker_vm_ip, target_vm_ip)

    @test.idempotent_id('1cb75005-e560-4fa3-a2fe-d0850fefcb49')
    @test.services('compute', 'network')
    def test_restart_vms(self):
        attacker_vm_ip, target_vm_ip = self._boot_servers()
        self.run_arp_poisoning_test(attacker_vm_ip, target_vm_ip)
        attacker_vm = self.servers['attacker_vm']
        target_vm = self.servers['target_vm']
        self.servers_client.stop_server(attacker_vm['id'])
        self.servers_client.stop_server(target_vm['id'])
        waiters.wait_for_server_status(self.servers_client,
                                       attacker_vm['id'], 'SHUTOFF')

        waiters.wait_for_server_status(self.servers_client,
                                       target_vm['id'], 'SHUTOFF')

        self.servers_client.start_server(attacker_vm['id'])
        self.servers_client.start_server(target_vm['id'])

        waiters.wait_for_server_status(self.servers_client, attacker_vm['id'],
                                       'ACTIVE')
        waiters.wait_for_server_status(self.servers_client, target_vm['id'],
                                       'ACTIVE')
        self.run_arp_poisoning_test(attacker_vm_ip, target_vm_ip)

    def _get_neutron_agents(self):
        agents = self.admin_manager.network_client.list_agents()['agents']
        filtered_agents = filter(
            lambda agent: 'vSwitch' or 'Linux Bridge' in agent['agent_type'],
            agents
        )
        return filtered_agents

    def _restart_neutron_agents(self):
        agents_to_restart = self._get_neutron_agents()
        for agent in agents_to_restart:
            self.admin_manager.network_client.update_agent(
                agent['id'], {"admin_state_up": False}
            )
        time.sleep(10)
        for agent in agents_to_restart:
            self.admin_manager.network_client.update_agent(
                agent['id'], {"admin_state_up": True}
            )

    @test.idempotent_id('f51200bd-d909-4ca6-8a1f-3ef92cf0cb78')
    @test.services('compute', 'network')
    def test_restart_neutron_agent(self):
        attacker_vm_ip, target_vm_ip = self._boot_servers()
        self.run_arp_poisoning_test(attacker_vm_ip, target_vm_ip)
        self._restart_neutron_agents()
        self.run_arp_poisoning_test(attacker_vm_ip, target_vm_ip)

    def _is_multi_compute_nodes(self):
        if len(self.compute_nodes) < 2:
            LOG.warning("TestArpPoisoning."
                        "Only one compute node available")
            return False
        return True

    def _prepare_multi_compute_nodes(self):
        for idx, node in enumerate(self.compute_nodes):
            create_kwargs = {
                'name': 'arp-agg-{}'.format(idx),
                'availability_zone': 'arp-avail-{}'.format(idx)
            }
            aggregate = self.admin_manager.aggregates_client. \
                create_aggregate(**create_kwargs)['aggregate']
            self.addCleanup(self.admin_manager.aggregates_client.
                            delete_aggregate, aggregate['id'])
            self.admin_manager.aggregates_client.add_host(
                aggregate['id'], node=node)
            self.addCleanup(self.admin_manager.aggregates_client.remove_host,
                            aggregate['id'], node=node)
            self.aggregates.append(aggregate['availability_zone'])

    @test.idempotent_id('67381e35-9661-497a-ae84-8643e4ebd905')
    @test.services('compute', 'network')
    def test_arp_poisoning_multiple_nodes(self):
        if self._is_multi_compute_nodes():
            self._prepare_multi_compute_nodes()
            attacker_vm_ip, target_vm_ip = self._boot_servers(
                multi_compute=True
            )
            self.run_arp_poisoning_test(attacker_vm_ip, target_vm_ip)
