# Copyright 2014 OpenStack Foundation
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

import netaddr

from tempest.api.network import base
from tempest.common.utils import data_utils
from tempest import config
from tempest.openstack.common import log as logging
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class NetworksTestPortsIPv6JSON(base.BaseNetworkTest):
    _interface = 'json'
    _ip_version = 6

    @classmethod
    def setUpClass(cls):
        super(NetworksTestPortsIPv6JSON, cls).setUpClass()
        msg = None
        if not CONF.network_feature_enabled.ipv6:
            msg = "IPv6 is not enabled"
        elif not CONF.network_feature_enabled.ipv6_subnet_attributes:
            msg = "DHCPv6 attributes are not enabled."
        if msg:
            raise cls.skipException(msg)
        cls.network = cls.create_network()

    def _clean_network(self):
        resp, body = self.client.list_ports()
        ports = body['ports']
        for port in ports:
            if self.ports:
                self.ports.pop()
            if port['device_owner'] == 'network:router_interface':
                self.client.remove_router_interface_with_port_id(
                    port['device_id'], port['id']
                )
            else:
                self.client.delete_port(port['id'])
        resp, body = self.client.list_subnets()
        subnets = body['subnets']
        for subnet in subnets:
            if self.subnets:
                self.subnets.pop()
            self.client.delete_subnet(subnet['id'])
        resp, body = self.client.list_routers()
        routers = body['routers']
        for router in routers:
            if self.routers:
                self.routers.pop()
            self.client.delete_router(router['id'])

    # Avoid race condition described in bug 1219795
    # by workaround function:
    def wr_bug1219795(self, subnet):
        dhcp_ip = subnet["allocation_pools"][0]["start"]
        _, body = self.client.list_ports()
        for dport in body['ports']:
            if dport['device_owner'] == 'network:dhcp' and dport['fixed_ips']:
                dhcp_ip = (netaddr.IPAddress(dhcp_ip) + 1).format()
                break
        return dhcp_ip

    def _create_subnets_and_port(self, kwargs1=None, kwargs2=None):
        kwargs1 = kwargs1 or {}
        kwargs2 = kwargs2 or {}
        subnet1 = self.create_subnet(self.network, **kwargs1)
        subnet2 = self.create_subnet(self.network, **kwargs2)
        port_mac = data_utils.rand_mac_address()
        port = self.create_port(self.network, mac_address=port_mac)
        return port, subnet1, subnet2

    def _port_ips(self, port):
        return [i['ip_address'] for i in port['fixed_ips']]

    def _eui64(self, port, sub):
        return data_utils.get_ipv6_addr_by_EUI64(
            sub['cidr'],
            port['mac_address'].lower()).format()

    @test.attr(type='smoke')
    def test_create_delete_subnet_with_v6_attributes(self):
        name = data_utils.rand_name('network-')
        # from https://www.dropbox.com/s/9bojvv9vywsz8sd/IPv6%20Two%20Modes%20v3.0.pdf
        ipv6_valid_modes_combinations = [('slaac', 'slaac'),
                                         ('dhcpv6-stateful', 'dhcpv6-stateful'),
                                         ('dhcpv6-stateless', 'dhcpv6-stateless'),
                                         ('dhcpv6-stateless', None),
                                         ('dhcpv6-stateful', None),
                                         ('slaac', None),
                                         (None, 'slaac'),
                                         (None, 'dhcpv6-stateless'),
                                         (None, 'dhcpv6-stateful'),
                                         (None, None)
                                        ]
        for ra_mode, address_mode in ipv6_valid_modes_combinations:
            resp, body = self.client.create_network(name=name)
            self.assertEqual('201', resp['status'])
            network = body['network']
            net_id = network['id']
            kwargs = {'gateway': 'fe80::1',
                      'ipv6_ra_mode': ra_mode,
                      'ipv6_address_mode': address_mode}
            kwargs = {k: v for k,v in kwargs.items() if v}
            subnet = self.create_subnet(network, **kwargs)
            # Verifies Subnet GW in IPv6
            self.assertEqual(subnet['gateway_ip'], 'fe80::1')
            self.assertEqual(subnet['ipv6_ra_mode'], ra_mode)
            self.assertEqual(subnet['ipv6_address_mode'], address_mode)
            # Delete network and subnet
            resp, body = self.client.delete_network(net_id)
            self.assertEqual('204', resp['status'])
            self.subnets.pop()

    @test.attr(type='smoke')
    def test_port_update_delete_46(self):
        """When 2 subnets configured with IPv6 SLAAC and IPv4
        port-update shall assign IP of subnets allocation pool.
        """
        for ra_mode, add_mode in (
                ('slaac', 'slaac'),
                ('dhcpv6-stateless', 'dhcpv6-stateless'),
        ):
            dhcp_kwargs = {'ipv6_ra_mode': ra_mode,
                           'ipv6_address_mode': add_mode}
            port, sub1, sub2 = self._create_subnets_and_port(
                kwargs1=dhcp_kwargs,
                kwargs2={'ip_version': 4})
            fixed_ips1 = [{'subnet_id': sub1['id']}]
            fixed_ips2 = [{'subnet_id': sub2['id']}]
            expected_ips = (self.wr_bug1219795(sub2), self._eui64(port, sub1))
            self.assertSequenceEqual(self._port_ips(port), expected_ips)
            port = self.update_port(port, fixed_ips=fixed_ips1)
            self.assertEqual(1, len(self._port_ips(port)))
            port = self.update_port(port, fixed_ips=fixed_ips1 + fixed_ips2)
            self.assertEqual(2, len(self._port_ips(port)))
            self.client.delete_port(port['id'])
            self.ports.pop()
            _, body = self.client.list_ports()
            ports_id_list = [i['id'] for i in body['ports']]
            self.assertNotIn(port['id'], ports_id_list)
            self._clean_network()

    @test.attr(type='smoke')
    def test_port_multiprefix_46(self):
        """When 4 subnets configured with IPv6 SLAAC and IPv4,
        the created port shall receive IPs from all of them..
        """
        for ra_mode, add_mode in (
                ('slaac', 'slaac'),
                ('dhcpv6-stateless', 'dhcpv6-stateless'),
                ('dhcpv6-stateful', 'dhcpv6-stateful'),
        ):
            kwargs = {'ipv6_ra_mode': ra_mode,
                      'ipv6_address_mode': add_mode}
            self.create_subnet(self.network, **kwargs)
        self.create_subnet(self.network, ip_version=4)
        port = self.create_port(self.network)
        self.assertEqual(4, len(self._port_ips(port)))
        self._clean_network()

    @test.attr(type='smoke')
    def test_port_multiprefix_46_router(self):
        """When 4 subnets configured with IPv6 SLAAC and IPv4,
        the created port shall receive IPs from all of them..
        Routers sending RAs shall not affect DHCP allocating.
        """
        subnets = []
        for ra_mode, add_mode in (
                ('slaac', 'slaac'),
                ('dhcpv6-stateless', 'dhcpv6-stateless'),
                ('dhcpv6-stateful', 'dhcpv6-stateful'),
        ):
            kwargs = {'ipv6_ra_mode': ra_mode,
                      'ipv6_address_mode': add_mode}
            subnets.append(self.create_subnet(self.network, **kwargs))
        subnets.append(self.create_subnet(self.network, ip_version=4))
        router = self.create_router(router_name="cisco",
                                        admin_state_up=True)
        for sub in subnets:
            self.create_router_interface(router['id'],
                                         sub['id'])
        port = self.create_port(self.network)
        self.assertEqual(4, len(self._port_ips(port)))
        self._clean_network()


    def tearDown(self):
        self._clean_network()
        super(NetworksTestPortsIPv6JSON, self).tearDown()
