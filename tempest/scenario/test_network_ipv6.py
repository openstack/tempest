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
from tempest.scenario import manager
from tempest import test
from tempest.common import sniffer
from tempest.common import radvd
from tempest.config import CONF


class TestNetworkIPv6(manager.NetworkScenarioTest):

    """This smoke test suite has the same assumption as TestNetworkBasicOps
    In addition, here we assume that network part of the cloud is configured
    either in IPv6 mode or in dual-stack mode.
    """
    _ip_version = 6

    network_resources = {'network': False, 'router': False, 'subnet': False,
                         'dhcp': False}

    @test.services('network')
    def test_large_prefix(self):
        import netaddr

        net = self._create_network(tenant_id=self.tenant_id,
                                   namestart='net-125-126')
        for bits in [125, 126]:
            sub = self._create_subnet(network=net,
                                      namestart='subnet-{0}'.format(bits),
                                      net_max_bits=bits)
            start = netaddr.IPAddress(sub.allocation_pools[0]['start'])
            end = netaddr.IPAddress(sub.allocation_pools[0]['end'])
            n_addresses = end.value - start.value + 1
            self.assertEqual(expected=pow(2, 128 - bits)-3,
                             observed=n_addresses)

    @test.services('compute', 'network')
    def test_46(self):
        image_id = CONF.compute.image_ref_alt
        ex_net = CONF.network.public_network_id
        net = self._create_network(tenant_id=self.tenant_id,
                                   namestart='net-46')

        def define_access(srv):
            for nic in srv.addresses[net.name]:
                if nic['version'] == 6:
                    srv.accessIPv6 = nic['addr']
                else:
                    srv.accessIPv4 = nic['addr']

        sub4 = self._create_subnet(network=net,
                                   namestart='sub-4',
                                   ip_version=4)
        self._create_subnet(network=net,
                            namestart='sub-6')
        router = self._get_router(tenant_id=self.tenant_id)
        sub4.add_to_router(router_id=router['id'])

        key_pair = self.create_keypair()
        sec_group = self._create_security_group_nova()
        kwargs = {'key_name': key_pair.id,
                  'security_groups': [sec_group.name]}

        i1 = self.create_server(create_kwargs=kwargs, image=image_id, flavor=1)
        i2 = self.create_server(create_kwargs=kwargs, image=image_id, flavor=1)

        fip1 = self._create_floating_ip(thing=i1, external_network_id=ex_net)
        fip2 = self._create_floating_ip(thing=i2, external_network_id=ex_net)
        define_access(i1)
        define_access(i2)

        ssh1 = self.get_remote_client(server_or_ip=fip1.floating_ip_address,
                                      username=CONF.compute.image_alt_ssh_user,
                                      private_key=key_pair.private_key)
        ssh2 = self.get_remote_client(server_or_ip=fip2.floating_ip_address,
                                      username=CONF.compute.image_alt_ssh_user,
                                      private_key=key_pair.private_key)

        r = ssh1.exec_command('ip addr show dev eth0')
        self.assertIn(i1.accessIPv4, r)
        self.assertIn(i1.accessIPv6, r)  # should fail if image not support v6
        r = ssh2.exec_command('ip addr show dev eth0')
        self.assertIn(i2.accessIPv4, r)
        self.assertIn(i2.accessIPv6, r)  # should fail if image not support v6
        r = ssh1.exec_command(cmd='ping -c1 {0}'.format(i2.accessIPv4))
        self.assertIn('0% packet loss', r)
        r = ssh2.exec_command(cmd='ping -c1 {0}'.format(i1.accessIPv4))
        self.assertIn('0% packet loss', r)
        r = ssh1.exec_command(cmd='ping6 -c1 {0}'.format(i2.accessIPv6))
        self.assertIn('0% packet loss', r)
        r = ssh2.exec_command(cmd='ping6 -c1 {0}'.format(i1.accessIPv6))
        self.assertIn('0% packet loss', r)



class TestRadvdIPv6(manager.NetworkScenarioTest):
    _ip_version = 6

    network_resources = {'network': True, 'router': True, 'subnet': True,
                         'dhcp': True, 'ip_version': 6}

    @test.services('compute', 'network')
    def test_internal_radvd(self):
        ex_net = CONF.network.public_network_id

        key_pair = self.create_keypair()
        sec_group = self._create_security_group_nova()
        kwargs = {'key_name': key_pair.id,
                  'security_groups': [sec_group.name]}
        server = self.create_server(create_kwargs=kwargs)
        r = sniffer.sniff(what=sniffer.SNIFF_RADVD, count=3)
        self.assertEqual(expected='icmp6', observed=r['what'])
        self.assertEqual(expected=3,
                         observed=r['count'],
                         message='Wrong number of radvd packets')
        self.assertEqual(expected=2,
                         observed=r['advertisement']['count'],
                         message='Wrong number of RA')
        self.assertEqual(expected=1,
                         observed=r['solicitation']['count'],
                         message='Wrong number of RS')

        if self.run_ssh:
            fip = self._create_floating_ip(thing=server,
                                           external_network_id=ex_net)
            server.add_floating_ip(fip.floating_ip_address)
            ssh = self.get_remote_client(server_or_ip=fip,
                                         private_key=key_pair.private_key)
            capture = ssh.exec_command(sniffer.sniff(what=sniffer.SNIFF_RADVD,
                                                     count=3,
                                                     is_remote=True))
            r = sniffer.sniff_analyzer_radvd(capture=capture)
            self.assertEqual(expected='icmp6', observed=r['what'])
            self.assertEqual(expected=3,
                             observed=r['count'],
                             message='Wrong number of radvd packets')
            self.assertEqual(expected=2,
                             observed=r['advertisement']['count'],
                             message='Wrong number of RA')
            self.assertEqual(expected=1,
                             observed=r['solicitation']['count'],
                             message='Wrong number of RS')

    @test.services('compute', 'network')
    def test_two_radvd(self):
        t_ex = sniffer.sniff_in_thread(what=sniffer.SNIFF_RADVD,
                                       interface='br-ex',
                                       count=100,
                                       timeout=120)
        t_in = sniffer.sniff_in_thread(what=sniffer.SNIFF_RADVD,
                                       interface='br-int',
                                       count=100,
                                       timeout=120)

        radvd.radvd_start_on(iface='br-ex', prefix='2009::/64')

        key_pair = self.create_keypair()
        sec_group = self._create_security_group_nova()
        kwargs = {'key_name': key_pair.id,
                  'security_groups': [sec_group.name]}
        self.create_server(create_kwargs=kwargs)

        t_ex.join()
        t_in.join()

        r_ex = t_ex.result
        r_in = t_in.result

        self.assertIn('2009::/64', r_ex['advertisement']['prefixes'])
        self.assertIn(CONF.network.public_network_ipv6_cidr,
                      r_in['advertisement']['prefixes'])
