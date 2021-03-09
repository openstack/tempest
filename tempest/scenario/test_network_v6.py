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

from oslo_log import log as logging

from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators
from tempest.lib import exceptions
from tempest.scenario import manager

CONF = config.CONF
LOG = logging.getLogger(__name__)


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
        if not (CONF.network_feature_enabled.ipv6 and
                CONF.network_feature_enabled.ipv6_subnet_attributes):
            raise cls.skipException('IPv6 or its attributes not supported')
        if not (CONF.network.project_networks_reachable or
                CONF.network.public_network_id):
            msg = ('Either project_networks_reachable must be "true", or '
                   'public_network_id must be defined.')
            raise cls.skipException(msg)
        if CONF.network.shared_physical_network:
            msg = 'Deployment uses a shared physical network'
            raise cls.skipException(msg)
        if not CONF.network_feature_enabled.floating_ips:
            raise cls.skipException("Floating ips are not available")

    @classmethod
    def setup_credentials(cls):
        # Create no network resources for these tests.
        cls.set_network_resources()
        super(TestGettingAddress, cls).setup_credentials()

    def setUp(self):
        super(TestGettingAddress, self).setUp()
        self.keypair = self.create_keypair()
        self.sec_grp = self.create_security_group()

    def prepare_network(self, address6_mode, n_subnets6=1, dualnet=False):
        """Prepare network

        Creates network with given number of IPv6 subnets in the given mode and
        one IPv4 subnet.
        Creates router with ports on all subnets.
        if dualnet - create IPv6 subnets on a different network
        :return: list of created networks
        """
        network = self.create_network()
        if dualnet:
            network_v6 = self.create_network()

        sub4 = self.create_subnet(network=network,
                                  namestart='sub4',
                                  ip_version=4)

        router = self.get_router()
        self.routers_client.add_router_interface(router['id'],
                                                 subnet_id=sub4['id'])

        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.routers_client.remove_router_interface,
                        router['id'], subnet_id=sub4['id'])

        self.subnets_v6 = []
        for _ in range(n_subnets6):
            net6 = network_v6 if dualnet else network
            sub6 = self.create_subnet(network=net6,
                                      namestart='sub6',
                                      ip_version=6,
                                      ipv6_ra_mode=address6_mode,
                                      ipv6_address_mode=address6_mode)

            self.routers_client.add_router_interface(router['id'],
                                                     subnet_id=sub6['id'])

            self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                            self.routers_client.remove_router_interface,
                            router['id'], subnet_id=sub6['id'])

            self.subnets_v6.append(sub6)
        return [network, network_v6] if dualnet else [network]

    @staticmethod
    def define_server_ips(srv):
        ips = {'4': None, '6': []}
        for nics in srv['addresses'].values():
            for nic in nics:
                if nic['version'] == 6:
                    ips['6'].append(nic['addr'])
                else:
                    ips['4'] = nic['addr']
        return ips

    def prepare_server(self, networks=None):
        username = CONF.validation.image_ssh_user

        srv = self.create_server(
            key_name=self.keypair['name'],
            security_groups=[{'name': self.sec_grp['name']}],
            networks=[{'uuid': n['id']} for n in networks])
        fip = self.create_floating_ip(server=srv)
        ips = self.define_server_ips(srv=srv)
        ssh = self.get_remote_client(
            ip_address=fip['floating_ip_address'],
            username=username, server=srv)
        return ssh, ips, srv

    def turn_nic6_on(self, ssh, sid, network_id):
        """Turns the IPv6 vNIC on

        Required because guest images usually set only the first vNIC on boot.
        Searches for the IPv6 vNIC's MAC and brings it up.

        @param ssh: RemoteClient ssh instance to server
        @param sid: server uuid
        @param network_id: the network id the NIC is connected to
        """
        ports = [
            p["mac_address"] for p in
            self.os_admin.ports_client.list_ports(
                device_id=sid, network_id=network_id)['ports']
        ]

        self.assertEqual(1, len(ports),
                         message=("Multiple IPv6 ports found on network %s. "
                                  "ports: %s")
                         % (network_id, ports))
        mac6 = ports[0]
        nic = ssh.get_nic_name_by_mac(mac6)
        # NOTE(slaweq): on RHEL based OS ifcfg file for new interface is
        # needed to make IPv6 working on it, so if
        # /etc/sysconfig/network-scripts directory exists ifcfg-%(nic)s file
        # should be added in it
        if self._sysconfig_network_scripts_dir_exists(ssh):
            try:
                ssh.exec_command(
                    'echo -e "DEVICE=%(nic)s\\nNAME=%(nic)s\\nIPV6INIT=yes" | '
                    'sudo tee /etc/sysconfig/network-scripts/ifcfg-%(nic)s; '
                    'sudo nmcli connection reload' % {'nic': nic})
                ssh.exec_command('sudo nmcli connection up %s' % nic)
            except exceptions.SSHExecCommandFailed as e:
                # NOTE(slaweq): Sometimes it can happen that this SSH command
                # will fail because of some error from network manager in
                # guest os.
                # But even then doing ip link set up below is fine and
                # IP address should be configured properly.
                LOG.debug("Error during restarting %(nic)s interface on "
                          "instance. Error message: %(error)s",
                          {'nic': nic, 'error': e})
        ssh.exec_command("sudo ip link set %s up" % nic)

    def _sysconfig_network_scripts_dir_exists(self, ssh):
        return "False" not in ssh.exec_command(
            'test -d /etc/sysconfig/network-scripts/ || echo "False"')

    def _prepare_and_test(self, address6_mode, n_subnets6=1, dualnet=False):
        net_list = self.prepare_network(address6_mode=address6_mode,
                                        n_subnets6=n_subnets6,
                                        dualnet=dualnet)

        sshv4_1, ips_from_api_1, srv1 = self.prepare_server(networks=net_list)
        sshv4_2, ips_from_api_2, srv2 = self.prepare_server(networks=net_list)

        def guest_has_address(ssh, addr):
            return addr in ssh.exec_command("ip address")

        # Turn on 2nd NIC for Cirros when dualnet
        if dualnet:
            _, network_v6 = net_list
            self.turn_nic6_on(sshv4_1, srv1['id'], network_v6['id'])
            self.turn_nic6_on(sshv4_2, srv2['id'], network_v6['id'])

        # get addresses assigned to vNIC as reported by 'ip address' utility
        ips_from_ip_1 = sshv4_1.exec_command("ip address")
        ips_from_ip_2 = sshv4_2.exec_command("ip address")
        self.assertIn(ips_from_api_1['4'], ips_from_ip_1)
        self.assertIn(ips_from_api_2['4'], ips_from_ip_2)
        for i in range(n_subnets6):
            # v6 should be configured since the image supports it
            # It can take time for ipv6 automatic address to get assigned
            for srv, ssh, ips in (
                    (srv1, sshv4_1, ips_from_api_1),
                    (srv2, sshv4_2, ips_from_api_2)):
                ip = ips['6'][i]
                result = test_utils.call_until_true(
                    guest_has_address,
                    CONF.validation.ping_timeout, 1, ssh, ip)
                if not result:
                    self.log_console_output(servers=[srv])
                    self.fail(
                        'Address %s not configured for instance %s, '
                        'ip address output is\n%s' %
                        (ip, srv['id'], ssh.exec_command("ip address")))

        self.check_remote_connectivity(sshv4_1, ips_from_api_2['4'])
        self.check_remote_connectivity(sshv4_2, ips_from_api_1['4'])

        for i in range(n_subnets6):
            self.check_remote_connectivity(sshv4_1,
                                           ips_from_api_2['6'][i])
            self.check_remote_connectivity(sshv4_1,
                                           self.subnets_v6[i]['gateway_ip'])
            self.check_remote_connectivity(sshv4_2,
                                           ips_from_api_1['6'][i])
            self.check_remote_connectivity(sshv4_2,
                                           self.subnets_v6[i]['gateway_ip'])

    @decorators.attr(type='slow')
    @decorators.idempotent_id('2c92df61-29f0-4eaa-bee3-7c65bef62a43')
    @utils.services('compute', 'network')
    def test_slaac_from_os(self):
        self._prepare_and_test(address6_mode='slaac')

    @decorators.attr(type='slow')
    @decorators.idempotent_id('d7e1f858-187c-45a6-89c9-bdafde619a9f')
    @utils.services('compute', 'network')
    def test_dhcp6_stateless_from_os(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless')

    @decorators.attr(type='slow')
    @decorators.idempotent_id('7ab23f41-833b-4a16-a7c9-5b42fe6d4123')
    @utils.services('compute', 'network')
    def test_multi_prefix_dhcpv6_stateless(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless', n_subnets6=2)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('dec222b1-180c-4098-b8c5-cc1b8342d611')
    @utils.services('compute', 'network')
    def test_multi_prefix_slaac(self):
        self._prepare_and_test(address6_mode='slaac', n_subnets6=2)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('b6399d76-4438-4658-bcf5-0d6c8584fde2')
    @utils.services('compute', 'network')
    def test_dualnet_slaac_from_os(self):
        self._prepare_and_test(address6_mode='slaac', dualnet=True)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('76f26acd-9688-42b4-bc3e-cd134c4cb09e')
    @utils.services('compute', 'network')
    def test_dualnet_dhcp6_stateless_from_os(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless', dualnet=True)

    @decorators.attr(type='slow')
    @decorators.idempotent_id('cf1c4425-766b-45b8-be35-e2959728eb00')
    @utils.services('compute', 'network')
    def test_dualnet_multi_prefix_dhcpv6_stateless(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless', n_subnets6=2,
                               dualnet=True)

    @decorators.idempotent_id('9178ad42-10e4-47e9-8987-e02b170cc5cd')
    @decorators.attr(type='slow')
    @utils.services('compute', 'network')
    def test_dualnet_multi_prefix_slaac(self):
        self._prepare_and_test(address6_mode='slaac', n_subnets6=2,
                               dualnet=True)
