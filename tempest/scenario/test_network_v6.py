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

from oslo_log import log as logging
import six

from tempest import config
from tempest.scenario import manager
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestGettingAddress(manager.NetworkScenarioTest):
    """Create network with subnets: one IPv4 and
    one or few IPv6 in a given address mode
    Boot 2 VMs on this network
    Allocate and assign 2 FIP4
    Check that vNICs of all VMs gets all addresses actually assigned
    Ping4 to one VM from another one
    If ping6 available in VM, do ping6 to all v6 addresses
    """

    @classmethod
    def skip_checks(cls):
        super(TestGettingAddress, cls).skip_checks()
        if not (CONF.network_feature_enabled.ipv6
                and CONF.network_feature_enabled.ipv6_subnet_attributes):
            raise cls.skipException('IPv6 or its attributes not supported')
        if not (CONF.network.tenant_networks_reachable
                or CONF.network.public_network_id):
            msg = ('Either tenant_networks_reachable must be "true", or '
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
        self.srv_kwargs = {
            'key_name': self.keypair['name'],
            'security_groups': [{'name': self.sec_grp['name']}]}

    def prepare_network(self, address6_mode, n_subnets6=1):
        """Creates network with
         given number of IPv6 subnets in the given mode and
         one IPv4 subnet
         Creates router with ports on all subnets
        """
        self.network = self._create_network(tenant_id=self.tenant_id)
        sub4 = self._create_subnet(network=self.network,
                                   namestart='sub4',
                                   ip_version=4,)

        router = self._get_router(tenant_id=self.tenant_id)
        sub4.add_to_router(router_id=router['id'])
        self.addCleanup(sub4.delete)

        for _ in range(n_subnets6):
            sub6 = self._create_subnet(network=self.network,
                                       namestart='sub6',
                                       ip_version=6,
                                       ipv6_ra_mode=address6_mode,
                                       ipv6_address_mode=address6_mode)

            sub6.add_to_router(router_id=router['id'])
            self.addCleanup(sub6.delete)

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

    def prepare_server(self):
        username = CONF.compute.image_ssh_user

        create_kwargs = self.srv_kwargs
        create_kwargs['networks'] = [{'uuid': self.network.id}]

        srv = self.create_server(create_kwargs=create_kwargs)
        fip = self.create_floating_ip(thing=srv)
        ips = self.define_server_ips(srv=srv)
        ssh = self.get_remote_client(
            server_or_ip=fip.floating_ip_address,
            username=username)
        return ssh, ips

    def _prepare_and_test(self, address6_mode, n_subnets6=1):
        self.prepare_network(address6_mode=address6_mode,
                             n_subnets6=n_subnets6)

        sshv4_1, ips_from_api_1 = self.prepare_server()
        sshv4_2, ips_from_api_2 = self.prepare_server()

        def guest_has_address(ssh, addr):
            return addr in ssh.get_ip_list()

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
                                                 CONF.compute.ping_timeout, 1))

            self.assertTrue(test.call_until_true(srv2_v6_addr_assigned,
                                                 CONF.compute.ping_timeout, 1))

        result = sshv4_1.ping_host(ips_from_api_2['4'])
        self.assertIn('0% packet loss', result)
        result = sshv4_2.ping_host(ips_from_api_1['4'])
        self.assertIn('0% packet loss', result)

        # Some VM (like cirros) may not have ping6 utility
        result = sshv4_1.exec_command('whereis ping6')
        is_ping6 = False if result == 'ping6:\n' else True
        if is_ping6:
            for i in range(n_subnets6):
                result = sshv4_1.ping_host(ips_from_api_2['6'][i])
                self.assertIn('0% packet loss', result)
                result = sshv4_2.ping_host(ips_from_api_1['6'][i])
                self.assertIn('0% packet loss', result)
        else:
            LOG.warning('Ping6 is not available, skipping')

    @test.idempotent_id('2c92df61-29f0-4eaa-bee3-7c65bef62a43')
    @test.services('compute', 'network')
    def test_slaac_from_os(self):
        self._prepare_and_test(address6_mode='slaac')

    @test.idempotent_id('d7e1f858-187c-45a6-89c9-bdafde619a9f')
    @test.services('compute', 'network')
    def test_dhcp6_stateless_from_os(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless')

    @test.idempotent_id('7ab23f41-833b-4a16-a7c9-5b42fe6d4123')
    @test.services('compute', 'network')
    def test_multi_prefix_dhcpv6_stateless(self):
        self._prepare_and_test(address6_mode='dhcpv6-stateless', n_subnets6=2)

    @test.idempotent_id('dec222b1-180c-4098-b8c5-cc1b8342d611')
    @test.services('compute', 'network')
    def test_multi_prefix_slaac(self):
        self._prepare_and_test(address6_mode='slaac', n_subnets6=2)
