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
import netaddr

from oslo_log import log as logging

from tempest import config
from tempest.scenario import manager
from tempest import test


CONF = config.CONF
LOG = logging.getLogger(__name__)


class TestGettingAddress(manager.NetworkScenarioTest):
    """Create network with 2 subnets: IPv4 and IPv6 in a given address mode
    Boot 2 VMs on this network
    Allocate and assign 2 FIP4
    Check that vNIC of server matches port data from OpenStack DB
    Ping4 tenant IPv4 of one VM from another one
    Will do the same with ping6 when available in VM
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

    def prepare_network(self, address6_mode):
        """Creates network with
         one IPv6 subnet in the given mode and
         one IPv4 subnet
         Creates router with ports on both subnets
        """
        self.network = self._create_network(tenant_id=self.tenant_id)
        sub4 = self._create_subnet(network=self.network,
                                   namestart='sub4',
                                   ip_version=4,)
        # since https://bugs.launchpad.net/neutron/+bug/1394112 we need
        # to specify gateway_ip manually
        net_range = netaddr.IPNetwork(CONF.network.tenant_network_v6_cidr)
        gateway_ip = (netaddr.IPAddress(net_range) + 1).format()
        sub6 = self._create_subnet(network=self.network,
                                   namestart='sub6',
                                   ip_version=6,
                                   gateway_ip=gateway_ip,
                                   ipv6_ra_mode=address6_mode,
                                   ipv6_address_mode=address6_mode)

        router = self._get_router(tenant_id=self.tenant_id)
        sub4.add_to_router(router_id=router['id'])
        sub6.add_to_router(router_id=router['id'])
        self.addCleanup(sub4.delete)
        self.addCleanup(sub6.delete)

    @staticmethod
    def define_server_ips(srv):
        for net_name, nics in srv['addresses'].iteritems():
            for nic in nics:
                if nic['version'] == 6:
                    srv['accessIPv6'] = nic['addr']
                else:
                    srv['accessIPv4'] = nic['addr']

    def prepare_server(self):
        username = CONF.compute.image_ssh_user

        create_kwargs = self.srv_kwargs
        create_kwargs['networks'] = [{'uuid': self.network.id}]

        srv = self.create_server(create_kwargs=create_kwargs)
        fip = self.create_floating_ip(thing=srv)
        self.define_server_ips(srv=srv)
        ssh = self.get_remote_client(
            server_or_ip=fip.floating_ip_address,
            username=username)
        return ssh, srv

    def _prepare_and_test(self, address6_mode):
        self.prepare_network(address6_mode=address6_mode)

        ssh1, srv1 = self.prepare_server()
        ssh2, srv2 = self.prepare_server()

        def guest_has_address(ssh, addr):
            return addr in ssh.get_ip_list()

        srv1_v6_addr_assigned = functools.partial(
            guest_has_address, ssh1, srv1['accessIPv6'])
        srv2_v6_addr_assigned = functools.partial(
            guest_has_address, ssh2, srv2['accessIPv6'])

        result = ssh1.get_ip_list()
        self.assertIn(srv1['accessIPv4'], result)
        # v6 should be configured since the image supports it
        # It can take time for ipv6 automatic address to get assigned
        self.assertTrue(
            test.call_until_true(srv1_v6_addr_assigned,
                                 CONF.compute.ping_timeout, 1))
        result = ssh2.get_ip_list()
        self.assertIn(srv2['accessIPv4'], result)
        # v6 should be configured since the image supports it
        # It can take time for ipv6 automatic address to get assigned
        self.assertTrue(
            test.call_until_true(srv2_v6_addr_assigned,
                                 CONF.compute.ping_timeout, 1))
        result = ssh1.ping_host(srv2['accessIPv4'])
        self.assertIn('0% packet loss', result)
        result = ssh2.ping_host(srv1['accessIPv4'])
        self.assertIn('0% packet loss', result)

        # Some VM (like cirros) may not have ping6 utility
        result = ssh1.exec_command('whereis ping6')
        is_ping6 = False if result == 'ping6:\n' else True
        if is_ping6:
            result = ssh1.ping_host(srv2['accessIPv6'])
            self.assertIn('0% packet loss', result)
            result = ssh2.ping_host(srv1['accessIPv6'])
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
