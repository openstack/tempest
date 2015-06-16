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
import collections
import re

from oslo_log import log as logging
from tempest_lib.common.utils import data_utils

from tempest import config
from tempest_lib import exceptions
from tempest.scenario import manager
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)

Floating_IP_tuple = collections.namedtuple('Floating_IP_tuple',
                                           ['floating_ip', 'server'])
ICMP_HEADER_LEN = 8


class TestNetworkMultiNode(manager.NetworkScenarioTest):

    """
    The Neutron ML2 driver will create a VLAN, when configured for VLAN, on the
    underlying network element when the first virtual machine (VM) is attached
    to a network/compute host.  Conversely, the ML2 driver will delete
    the VLAN associated with a network/compute host when the last VM is
    removed from that network/compute host.

    This test is designed for a multi-node OpenStack deployment
    with the goal of creating the maximum number of network create and
    delete events given the available resources.

    The test does the following:

    * Creates Aggregates/Zones with a one to one mapping of compute host
      to zone.  This allows the test to place a VM on a particular compute
      host.
    * Create networks based on the number of VMs and compute hosts.
    * Create VMs and distribute them on networks.
    * Selects one of the VMs as a ping source to send ping packets to each
      of the other (east/west) VMs using both the floating IP and the fixed
      IP address.  The number of ping packets and the size of the ping
      packets are controlled by the following tempest
      configuration variables:
       - test_packet_count: The number of packets to send for each packet size
       - test_packet_sizes: A list of packet sizes used during testing
      The packet and byte counts are verified for each ping test sequence.
    * The VMs are then deleted, not as part of test cleanup but to allow the
      network delete events from the ML2 driver to be captured and verified.
    """

    credentials = ['primary', 'admin']

    @classmethod
    def resource_setup(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(TestNetworkMultiNode, cls).resource_setup()

    @classmethod
    def skip_checks(cls):
        super(TestNetworkMultiNode, cls).skip_checks()
        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            cls.enabled = False
            raise exceptions.InvalidConfiguration(msg)

        for ext in ['router', 'security-group']:
            if not test.is_extension_enabled(ext, 'network'):
                msg = "%s extension not enabled." % ext
                raise exceptions.InvalidConfiguration(msg)

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(TestNetworkMultiNode, cls).setup_credentials()
        # Use admin client by default
        cls.manager = cls.admin_manager

    def _delete_aggregate(self, aggregate):
        self.aggregates_client.delete_aggregate(aggregate['id'])

    def _add_host(self, aggregate_id, host):
        aggregate = self.aggregates_client.add_host(aggregate_id, host)
        self.addCleanup(self._remove_host, aggregate['id'], host)
        self.assertIn(host, aggregate['hosts'])

    def _remove_host(self, aggregate_id, host):
        aggregate = self.aggregates_client.remove_host(aggregate_id, host)
        self.assertNotIn(host, aggregate['hosts'])

    def _create_server(self, name, network, zone=None):
        create_kwargs = self.srv_kwargs
        create_kwargs['networks'] = [{'uuid': network.id}]
        if zone is not None:
            create_kwargs['availability_zone'] = zone
        server = self.create_server(name=name, create_kwargs=create_kwargs)
        return dict(server=server, keypair=self.keypair)

    def setup_aggregates(self):
        """
        Setup Aggregates/Zones - one compute host per zone so that the test
        can control which compute host the VMs land on.
        """
        self.aggregates_client = self.manager.aggregates_client
        self.hypervisor_client = self.manager.hypervisor_client
        self.hypervisors_list = self.hypervisor_client.get_hypervisor_list()

        # Verify the hypervisors are operational and make a list
        # of them for later use
        self.hypervisors = []
        self.aggregates = []
        i = 0
        for hypervisor in self.hypervisors_list:
            if hypervisor['status'] == 'enabled':
                if hypervisor['state'] == 'up':
                    self.hypervisors.append(hypervisor)
                    # Create an aggregate/zone per hypervisor host
                    name = data_utils.rand_name('Agg')
                    aggregate_kwargs = {
                        'name': '{0}'.format(name),
                        'availability_zone': '{0}-Zone{1}'.format(name, i)
                    }
                    i += 1
                    aggregate = self.aggregates_client.create_aggregate(
                        **aggregate_kwargs)
                    self.addCleanup(self._delete_aggregate, aggregate)
                    self.aggregates.append(aggregate)
                    self._add_host(aggregate['id'],
                                   hypervisor['hypervisor_hostname'])

    def setUp(self):
        super(TestNetworkMultiNode, self).setUp()
        self.keypair = self.create_keypair()
        self.floating_ip_tuples = []
        self.linux_client = None
        self.private_key = None
        self.servers = {}
        self.srv_kwargs = {'key_name': self.keypair['name']}
        self.tenant_id = self.manager.identity_client.tenant_id
        self.total_expected_pkts = 0
        self.total_expected_bytes = 0
        self.segmentation_ids = []
        self.number_instances_per_compute = 1
        self.number_routers_per_tenant = 1

        # Classes that inherit this class can redefine packet size/count
        # based on their own needs or accept the default in the CONF
        if not hasattr(self, 'test_packet_sizes'):
            self.test_packet_sizes = map(int, CONF.scenario.test_packet_sizes)

        if not hasattr(self, 'test_packet_count'):
            self.test_packet_count = CONF.scenario.test_packet_count

        if not hasattr(self, 'max_instances_per_tenant'):
            self.max_instances_per_tenant = (
                CONF.scenario.max_instances_per_tenant)

        # Allows the ability to place VMs on specific compute nodes
        self.setup_aggregates()

        self.num_networks = int(self.max_instances_per_tenant /
                                len(self.hypervisors))

        LOG.debug("Max instances per tenant = {0}".
                  format(self.max_instances_per_tenant))
        LOG.debug("Number of instances per Network/compute = {0}".
                  format(self.number_instances_per_compute))
        LOG.debug("Number of Networks = {0}".format(self.num_networks))

        self.security_group = self._create_security_group(
            tenant_id=self.tenant_id)
        self.srv_kwargs['security_groups'] = [self.security_group]
        try:
            self._create_loginable_secgroup_rule(secgroup=self.security_group)
        except Exception as e:
            LOG.debug("Login sec group already exists: {0}".format(e))

        self.setup_networks()
        self.setup_vms()

    def add_network(self, client=None, tenant_id=None, router=None):
        if CONF.baremetal.driver_enabled:
            network = self._get_network_by_name(
                CONF.compute.fixed_network_name)
            router = None
            subnet = None
        else:
            network = self._create_network(client=client, tenant_id=tenant_id)
            if router is None:
                router = self._get_router(client=client, tenant_id=tenant_id)
            subnet = self._create_subnet(network=network, client=client)
            subnet.add_to_router(router.id)
        return network, subnet, router

    def setup_networks(self):
        self.networks = []
        router = None
        for i in range(0, self.num_networks):
            if i % (self.num_networks / self.number_routers_per_tenant) is 0:
                router = None
            self.network, self.subnet, router = self.add_network(
                tenant_id=self.tenant_id, router=router)
            self.networks.append(self.network)
            segmentation_id = self.network['provider:segmentation_id']
            self.segmentation_ids.append(segmentation_id)

    def setup_vms(self):
        # Create a VM on a each hypervisor per network
        for network in self.networks:
            for aggregate in self.aggregates:
                name = data_utils.rand_name('server')
                server_dict = self._create_server(name,
                                                  network,
                                                  zone=aggregate[
                                                      'availability_zone'])
                id = server_dict['server']['id']
                self.servers_client.wait_for_server_status(id, 'ACTIVE')
                self.assertIsNotNone(server_dict)
                self.servers[id] = server_dict['keypair']

    def delete_vms(self):
        """
        This method is not designed for clean up at the end of the test.  Some
        tests will need to verify that network delete events occur when the VMs
        are deleted.
        :return:
        """
        for server in self.servers.keys():
            LOG.debug("Deleting server {0}".format(server))
            self.servers_client.delete_server(server)
            self.servers_client.wait_for_server_termination(server)
            del self.servers[server]

    def verify_network_create_events(self):
        """
        Implement in network element specific test class
        """
        pass

    def verify_network_delete_events(self):
        """
        Implement in network element specific test class
        """
        pass

    def verify_network_element_ready(self):
        """
        Implement in network element specific test class
        """
        pass

    def verify_network_element_traffic_flows(self):
        """
        Implement in network element specific test class
        """
        pass

    def _ping_east_west(self, linux_client, target_ip,
                        count=CONF.compute.ping_count,
                        size=CONF.compute.ping_size):
        """
        From a remote linux host ping an IP address and return a
        data structure containing the results.
        :param linux_client: A remote_client object
        :param target_ip: The IP Address to ping from the remote client
        :param count: How many pings
        :param size: The packet size for each ping
        :return: A dictionary with received pkts/byts, summary, round-trip data
        """
        ping_data = {}
        bytes_rx = 0
        pkts_rx = 0

        # RegEx for data mining the ping results.
        pings = re.compile(r"""
                    ^(\d+)\sbytes\sfrom\s       # Store num bytes
                    ([\d\.]+):\s                # Store the IP address
                    (icmp_)?seq=(\d+)\s         # Account for Cirros diff and
                                                # store seq num
                    ttl=(\d+)\s                 # Store ttl
                    time=([\d\.]+)\sms          # Store time
                    """, re.VERBOSE | re.IGNORECASE)

        pings_summary = re.compile(r"""
                            ^(\d+)                      # Store num transmitted
                            \spackets\stransmitted,\s   # Common to all
                            (\d+)\s                     # Store num received
                            (packets[ ])?received,\s    # Cirros is different
                            (\d+)[%]\spacket\sloss      # Store pkt loss
                            ([, ]+time[ ](\d+)ms)?      # Cirros is different
                            """, re.VERBOSE | re.IGNORECASE)

        round_trip = re.compile(r"""
                                ^(rtt|round-trip)\s
                                min/avg/max(/mdev)?\s=\s
                                ([\d\.]+)[/]           # Store min time
                                ([\d\.]+)[/]           # Store avg time
                                ([\d\.]+)              # Store max time
                                .*""", re.VERBOSE | re.IGNORECASE)
        ping_result = None
        for x in range(0, 3):
            try:
                if CONF.scenario.advanced_vm_capabilities:
                    ping_result = linux_client.ping_host(
                        target_ip,
                        count=count,
                        size=size,
                        interval=.2).splitlines()
                else:
                    ping_result = linux_client.ping_host(
                        target_ip,
                        count=count,
                        size=size).splitlines()
                break
            except exceptions.SSHExecCommandFailed:
                LOG.debug("SSHExecCommandFailed - retrying")

        self.assertIsNotNone(ping_result,
                             "SSHExecCommandFailed - ping failed")
        if ping_result is not None and len(ping_result) >= count:
            for line in ping_result:

                m = pings.match(line)
                if m is not None:
                    bytes_rx += int(m.group(1))
                    pkts_rx += 1
                    continue

                m = pings_summary.match(line)
                if m is not None:
                    ping_data['summary'] = {'pkts_tx': int(m.group(1)),
                                            'pkts_rx': int(m.group(2)),
                                            'loss': int(m.group(4))}
                    continue

                m = round_trip.match(line)
                if m is not None:
                    ping_data['round-trip'] = {'min': float(m.group(3)),
                                               'ave': float(m.group(4)),
                                               'max': float(m.group(5))}
                    continue

        ping_data['data-received'] = {'packets': pkts_rx, 'bytes': bytes_rx}
        return ping_data

    def setup_linux_client(self):
        fip_tuple = self.floating_ip_tuples[0]
        self.linux_client_ip, server = fip_tuple
        self.private_key = self.servers[server['id']]['private_key']

        self.linux_client = self.get_remote_client(
            server_or_ip=self.linux_client_ip.
            floating_ip_address,
            private_key=self.private_key)

        super(TestNetworkMultiNode, self).check_vm_connectivity(
            self.linux_client_ip.floating_ip_address,
            username=CONF.compute.image_ssh_user,
            private_key=self.private_key,
            should_connect=True)

    def ping_target_ip(self,
                       linux_client,
                       source_ip,
                       target_ip,
                       pkt_size=CONF.compute.ping_size):
        LOG.debug("Ping from {0} to {1}".format(source_ip, target_ip))
        LOG.debug("Testing with packet size {0}".format(pkt_size))
        ping_result = self._ping_east_west(linux_client,
                                           target_ip,
                                           count=self.test_packet_count,
                                           size=pkt_size)

        self.assertIsNotNone(ping_result,
                             "Ping from {0} to {1} failed".
                             format(source_ip, target_ip))

        msg = "Ping result indicates packet loss from {0} to {1}".format(
            source_ip, target_ip)
        self.assertEqual(0, ping_result['summary']['loss'], msg)

        # Calculate expected pkts/bytes
        self.total_expected_pkts += self.test_packet_count
        self.total_expected_bytes += self.test_packet_count * (pkt_size +
                                                               ICMP_HEADER_LEN)
        # Store actual pkts/bytes used later for test
        self.total_actual_pkts += int(ping_result['data-received']['packets'])
        self.total_actual_bytes += int(ping_result['data-received']['bytes'])

    def verify_vm_to_vm_connectivity(self):
        """
        Selects one of the VMs created and uses it as a ping source to
        ping all other VMs.
        :return:
        """
        self.assertTrue(len(self.servers) >= 2,
                        "Not enough servers to check VM to VM connectivity")

        self.total_actual_pkts = 0
        self.total_actual_bytes = 0
        self.total_expected_pkts = 0
        self.total_expected_bytes = 0

        if self.linux_client is None:
            self.setup_linux_client()

        # Cycle through the VMs pinging each one from the testing VM
        # First use floating IPs and fixed IPs
        if self.floating_ip_tuples is not None:
            for i in range(1, len(self.floating_ip_tuples)):
                fip_tuple = self.floating_ip_tuples[i]
                target_ip, server = fip_tuple
                for pkt_size in self.test_packet_sizes:
                    self.ping_target_ip(self.linux_client,
                                        self.linux_client_ip.
                                        floating_ip_address,
                                        target_ip.floating_ip_address,
                                        pkt_size)

                    self.ping_target_ip(self.linux_client,
                                        self.linux_client_ip.
                                        floating_ip_address,
                                        target_ip.fixed_ip_address,
                                        pkt_size)

        LOG.debug("Received {0} Packets "
                  "containing {1} bytes".format(self.total_actual_pkts,
                                                self.total_actual_bytes))
        LOG.debug("Expected {0} Packets "
                  "containing {1} bytes".format(self.total_expected_pkts,
                                                self.total_expected_bytes))
        self.assertEqual(self.total_expected_pkts,
                         self.total_actual_pkts,
                         "Total packets received failed")

        self.assertEqual(self.total_expected_bytes,
                         self.total_actual_bytes,
                         "Total bytes received failed")

    def create_floating_ips(self):
        for server_id in self.servers.keys():
            server = {'id': server_id, 'tenant_id': self.tenant_id}
            floating_ip = self.create_floating_ip(server)
            self.floating_ip_tuple = Floating_IP_tuple(floating_ip, server)
            self.floating_ip_tuples.append(self.floating_ip_tuple)

    def delete_floating_ips(self):
        if self.floating_ip_tuples is not None:
            for i in range(0, len(self.floating_ip_tuples)):
                fip_tuple = self.floating_ip_tuples.pop()
                floating_ip, server = fip_tuple
                self._disassociate_floating_ip(floating_ip)

    def verify_vm_connectivity(self):
        if self.floating_ip_tuples is not None:
            for i in range(1, len(self.floating_ip_tuples)):
                fip_tuple = self.floating_ip_tuples[i]
                target_ip, server = fip_tuple
                msg = "Timeout waiting for %s" % target_ip.floating_ip_address

                self.assertTrue(self.
                                ping_ip_address(target_ip.floating_ip_address,
                                                should_succeed=True),
                                msg=msg)

    @test.idempotent_id('094f246d-9800-4c79-b249-361dab5d5a0f')
    @test.services('compute', 'network')
    def test_network_multi_node(self):
        self.verify_network_create_events()
        self.create_floating_ips()
        self.verify_vm_connectivity()
        self.verify_network_element_ready()
        self.verify_vm_to_vm_connectivity()
        self.verify_network_element_traffic_flows()
        self.delete_vms()
        self.verify_network_delete_events()

