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

    @test.services('network')
    def test_large_prefix(self):
        import netaddr

        net = self ._create_network(tenant_id=self.tenant_id,
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