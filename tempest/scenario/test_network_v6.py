# Copyright 2014 Cisco Systems, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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
import functools

import six

from tempest import config
from tempest.scenario import manager
from tempest import test


CONF = config.CONF


class TestGettingAddress(manager.NetworkScenarioTest):
    """Test Summary:

    1. Create network with subnets:
        1.1. one IPv4 and
        1.2. one or more IPv6 in a given address mode
    2. Boot 2 VMs on this network
    3. Allocate and assign 2 FIP4
    4. Check that vNICs of all VMs gets all addresses actually assigned
    5. Each VM will ping the other's v4 private address
    6. If ping6 available in VM, each VM will ping all of the other's  v6
       addresses as well as the router's
    """

    @classmethod
    def skip_checks(cls):
        super(TestGettingAddress, cls).skip_checks()
        if not (CONF.network_feature_enabled.ipv6
                and CONF.network_feature_enabled.ipv6_subnet_attributes):
            raise cls.skipException('IPv6 or its attributes not supported')
        if not (CONF.network.project_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            raise cls.skipException(msg)
        if CONF.baremetal.driver_enabled:
            msg = ('Baremetal does not currently support network isolation')
            raise cls.skipException(msg)

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(TestGettingAddress, cls).setup_credentials()

    def setUp(self):
        super(TestGettingAddress, self).setUp()
        self.keypair = self.create_keypair()
        self.sec_grp = self._create_security_group(tenant_id=self.tenant_id)

    def prepare_network(self, address6_mode, n_subnets6=1, dualnet=False):
        """Prepare network

        Creates network with given number of IPv6 subnets in the given mode and
        one IPv4 subnet.
        Creates router with ports on all subnets.
        if dualnet - create IPv6 subnets on a different network
        :return: list of created networks
        """
        self.network = self._create_network(tenant_id=self.tenant_id)
        if dualnet:
            self.network_v6 = self._create_network(tenant_id=self.tenant_id)

        sub4 = self._create_subnet(network=self.network,
                                   namestart='sub4',
                                   ip_version=4)

        router = self._get_router(tenant_id=self.tenant_id)
        sub4.add_to_router(router_id=router['id'])
        self.addCleanup(sub4.delete)

        self.subnets_v6 = []
        for _ in range(n_subnets6):
            net6 = self.network_v6 if dualnet else self.network
            sub6 = self._create_subnet(network=net6,
                                       namestart='sub6',
                                       ip_version=6,
                                       ipv6_ra_mode=address6_mode,
                                       ipv6_address_mode=address6_mode)

            sub6.add_to_router(router_id=router['id'])
            self.addCleanup(sub6.delete)
            self.subnets_v6.append(sub6)

        return [self.network, self.network_v6] if dualnet else [self.network]

    @staticmethod
    def define_server_ips(srv):
        ips = {'4': None, '6': []}
        for net_name, nics in six.iteritems(srv['addresses']):
            for nic in nics:
                if nic['version'] == 6:
                    ips['6'].append(nic['addr'])
                else:
                    ips['4'] = nic['addr']
        return ips

    def prepare_server(self, networks=None):
        username = CONF.validation.image_ssh_user

        networks = networks or [self.network]

        srv = self.create_server(
            key_name=self.keypair['name'],
            security_groups=[{'name': self.sec_grp['name']}],
            networks=[{'uuid': n.id} for n in networks],
            wait_until='ACTIVE')
        fip = self.create_floating_ip(thing=srv)
        ips = self.define_server_ips(srv=srv)
        ssh = self.get_remote_client(
            ip_address=fip.floating_ip_address,
            username=username)
        return ssh, ips, srv["id"]

    def turn_nic6_on(self, ssh, sid):
        """Turns the IPv6 vNIC on

        Required because guest images usually set only the first vNIC on boot.
        Searches for the IPv6 vNIC's MAC and brings it up.

        @param ssh: RemoteClient ssh instance to server
        @param sid: server uuid
        """
        ports = [p["mac_address"] for p in
                 self._list_ports(device_id=sid,
                                  network_id=self.network_v6.id)]
        self.assertEqual(1, len(ports),
                         message=("Multiple IPv6 ports found on network %s. "
                                  "ports: %s")
                         % (self.network_v6, ports))
        mac6 = ports[0]
        ssh.set_nic_state(ssh.get_nic_name_by_mac(mac6))

    def _prepare_and_test(self, address6_mode, n_subnets6=1, dualnet=False):
        net_list = self.prepare_network(address6_mode=address6_mode,
                                        n_subnets6=n_subnets6,
                                        dualnet=dualnet)

        sshv4_1, ips_from_api_1, sid1 = self.prepare_server(networks=net_list)
        sshv4_2, ips_from_api_2, sid2 = self.prepare_server(networks=net_list)

        def guest_has_address(ssh, addr):
            return addr in ssh.get_ip_list()

        # Turn on 2nd NIC for Cirros when dualnet
        if dualnet:
            self.turn_nic6_on(sshv4_1, sid1)
            self.turn_nic6_on(sshv4_2, sid2)

        # get addresses assigned to vNIC as reported by 'ip address' utility
        ips_from_ip_1 = sshv4_1.get_ip_list()
        ips_from_ip_2 = sshv4_2.get_ip_list()
        self.assertIn(ips_from_api_1['4'], ips_from_ip_1)
        self.assertIn(ips_from_api_2['4'], ips_from_ip_2)
        for i in range(n_subnets6):
            # v6 should be configured since the image supports it
            # It can take time for ipv6 automatic address to get assigned
            srv1_v6_addr_assigned = functools.partial(
                guest_has_address, sshv4_1, ips_from_api_1['6'][i])

            srv2_v6_addr_assigned = functools.partial(
                guest_has_address, sshv4_2, ips_from_api_2['6'][i])

            self.assertTrue(test.call_until_true(srv1_v6_addr_assigned,
                            CONF.validation.ping_timeout, 1))

            self.assertTrue(test.call_until_true(srv2_v6_addr_assigned,
                            CONF.validation.ping_timeout, 1))

        self._check_connectivity(sshv4_1, ips_from_api_2['4'])
        self._check_connectivity(sshv4_2, ips_from_api_1['4'])

        for i in range(n_subnets6):
            self._check_connectivity(sshv4_1,
                                     ips_from_api_2['6'][i])
            self._check_connectivity(sshv4_1,
                                     self.subnets_v6[i].gateway_ip)
            self._check_connectivity(sshv4_2,
                                     ips_from_api_1['6'][i])
            self._check_connectivity(sshv4_2,
                                     self.subnets_v6[i].gateway_ip)

    def _check_connectivity(self, source, dest):
        self.assertTrue(
            self._check_remote_connectivity(source, dest),
            "Timed out waiting for %s to become reachable from %s" %
            (dest, source.ssh_client.host)
        )

    @test.attr(type='slow')
    @test.idempotent_id('2c92df61-29f0-4eaa-bee3-7c65bef62a43')
    @test.services('compute', 'network')
    def test_slaac_from_os(self):
        self._prepare_and_test(address6_mode='slaac')

    @test.attr(type='slow')
    @test.idempotent_id('d7e1f858-187c-45a6-89c9-bdafde619a9f')
    @test.services('compute', 'network')
    def test_dhcp6_stateless_from_os(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless')

    @test.attr(type='slow')
    @test.idempotent_id('7ab23f41-833b-4a16-a7c9-5b42fe6d4123')
    @test.services('compute', 'network')
    def test_multi_prefix_dhcpv6_stateless(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless', n_subnets6=2)

    @test.attr(type='slow')
    @test.idempotent_id('dec222b1-180c-4098-b8c5-cc1b8342d611')
    @test.services('compute', 'network')
    def test_multi_prefix_slaac(self):
        self._prepare_and_test(address6_mode='slaac', n_subnets6=2)

    @test.attr(type='slow')
    @test.idempotent_id('b6399d76-4438-4658-bcf5-0d6c8584fde2')
    @test.services('compute', 'network')
    def test_dualnet_slaac_from_os(self):
        self._prepare_and_test(address6_mode='slaac', dualnet=True)

    @test.attr(type='slow')
    @test.idempotent_id('76f26acd-9688-42b4-bc3e-cd134c4cb09e')
    @test.services('compute', 'network')
    def test_dualnet_dhcp6_stateless_from_os(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless', dualnet=True)

    @test.idempotent_id('cf1c4425-766b-45b8-be35-e2959728eb00')
    @test.services('compute', 'network')
    def test_dualnet_multi_prefix_dhcpv6_stateless(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless', n_subnets6=2,
                               dualnet=True)

    @test.idempotent_id('9178ad42-10e4-47e9-8987-e02b170cc5cd')
    @test.services('compute', 'network')
    def test_dualnet_multi_prefix_slaac(self):
        self._prepare_and_test(address6_mode='slaac', n_subnets6=2,
                               dualnet=True)
