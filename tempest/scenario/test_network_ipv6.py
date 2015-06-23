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


class TestNetworkIPv6(manager.NetworkScenarioTest):

    """This smoke test suite has the same assumption as TestNetworkBasicOps
    In addition, here we assume that network part of the cloud is configured
    either in IPv6 mode or in dual-stack mode.
    """
    _ip_version = 6

    network_resources = {'network': False, 'router': False, 'subnet': False,
                         'dhcp': False}

    def _number_of_addresses_for_net_bits(self, net_bits):
        import netaddr

        net = self._create_network(tenant_id=self.tenant_id,
                                   namestart='net-125-126')
        sub = self._create_subnet(network=net,
                                  namestart='subnet-{0}'.format(net_bits),
                                  net_max_bits=net_bits,
                                  enable_dhcp=False)
        start = netaddr.IPAddress(sub.allocation_pools[0]['start'])
        end = netaddr.IPAddress(sub.allocation_pools[0]['end'])
        return end.value - start.value + 1

    @test.idempotent_id('2bddab74-257a-4341-8c7b-889198c6542a')
    @test.services('network')
    def test_large_prefix_125(self):
        self.assertEqual(expected=8,
                         observed=self._number_of_addresses_for_net_bits(125),
                         message='::/125 should have 8 addresses')

    @test.idempotent_id('13b9cb6b-c41b-4583-805d-df6a812ff6ed')
    @test.services('network')
    def test_large_prefix_126(self):
        self.assertEqual(expected=4,
                         observed=self._number_of_addresses_for_net_bits(126),
                         message='::/126 should have 4 addresses')
