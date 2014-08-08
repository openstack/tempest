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
#from test_network_basic_ops import TestNetworkBasicOps


class TestNetworkIPv6(manager.NetworkScenarioTest):

    """This smoke test suite has the same assumption as TestNetworkBasicOps
    In addition, here we assume that network part of the cloud is configured
    either in IPv6 mode or in dual-stack mode.
    """
    _ip_version = 6

    network_resources = {'network': False, 'router': False, 'subnet': False,
                         'dhcp': False}

    def test_large_prefix(self):
        net = self ._create_network(tenant_id=self.tenant_id,
                                    namestart='net-125')
        for bits in [125, 126]:
            sub = self._create_subnet(network=net, namestart='subnet-125',
                                      net_bits=bits)
            start = int(sub.allocation_pools[0]['start'].split('::')[-1], 16)
            end = int(sub.allocation_pools[0]['end'].split('::')[-1], 16)
            n_addresses = end - start + 1
            self.assertEqual(expected=pow(2, 128 - bits)-3,
                             observed=n_addresses)