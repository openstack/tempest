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

from tempest.api.network import base
from tempest import test


class HorizonIpv6Specifics(base.BaseNetworkTest):
    _ip_version = 6

    def tearDown(self):
        if self.port_id:
            self.ports_client.delete_port(self.port_id)
        super(HorizonIpv6Specifics, self).tearDown()

    @test.idempotent_id('7751edbf-b3d3-459b-b602-d5f689945722')
    def test_all(self):
        import netaddr
        """Tests number of API calls related ip IPv6 and used by Horizon
        """
        network = self.create_network()
        self.port_id = None

        cidr = '2014:abcd:ef00::/64'
        gateway_ip = cidr.replace('/64', '1')
        port1 = cidr.replace('/64', '2')

        self.create_subnet(network=network,
                                  cidr=netaddr.IPNetwork('2014:abcd:ef00::/64'),
                                  ip_version=self._ip_version,
                                  enable_dhcp=False)

        body = self.networks_client.list_networks()
        network_names = [net['name'] for net in body['networks']]
        self.assertIn(network['name'], network_names)

        body = self.subnets_client.list_subnets()

        ip_v6_subnet = filter(lambda s: s['ip_version'] == 6,
                              body['subnets'])[0]
        self.assertEqual(expected=cidr, observed=ip_v6_subnet['cidr'])
        self.assertEqual(expected=gateway_ip,
                         observed=ip_v6_subnet['gateway_ip'])

        body = self.ports_client.create_port(network_id=network['id'])
        self.port_id = body['port']['id']

        body = self.ports_client.list_ports()
        ips = [port['fixed_ips'][0]['ip_address'] for port in body['ports']]
        self.assertIn(port1, ips)
