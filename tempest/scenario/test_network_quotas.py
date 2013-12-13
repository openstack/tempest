# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from neutronclient.common import exceptions as exc

from tempest.scenario.manager import NetworkScenarioTest
from tempest.test import services


class TestNetworkQuotaBasic(NetworkScenarioTest):
    """
    This test suite contains tests that each loop trying to grab a
    particular resource until a quota limit is hit.
    For sanity, there is a maximum number of iterations - if this is hit
    the test fails. Covers network, subnet, port.
    """

    @classmethod
    def check_preconditions(cls):
        super(TestNetworkQuotaBasic, cls).check_preconditions()

    @classmethod
    def setUpClass(cls):
        super(TestNetworkQuotaBasic, cls).setUpClass()
        cls.check_preconditions()
        cls.networks = []
        cls.subnets = []
        cls.ports = []

    @services('network')
    def test_create_network_until_quota_hit(self):
        hit_limit = False
        networknum = self._get_tenant_own_network_num(self.tenant_id)
        max = self._show_quota_network(self.tenant_id) - networknum
        for n in xrange(max):
            try:
                self.networks.append(
                    self._create_network(self.tenant_id,
                                         namestart='network-quotatest-'))
            except exc.NeutronClientException as e:
                if (e.status_code != 409):
                    raise
                hit_limit = True
                break
        self.assertFalse(hit_limit, "Failed: Hit quota limit !")

        try:
            self.networks.append(
                self._create_network(self.tenant_id,
                                     namestart='network-quotatest-'))
        except exc.NeutronClientException as e:
            if (e.status_code != 409):
                raise
            hit_limit = True
        self.assertTrue(hit_limit, "Failed: Did not hit quota limit !")

    @services('network')
    def test_create_subnet_until_quota_hit(self):
        if not self.networks:
            self.networks.append(
                self._create_network(self.tenant_id,
                                     namestart='network-quotatest-'))
        hit_limit = False
        subnetnum = self._get_tenant_own_subnet_num(self.tenant_id)
        max = self._show_quota_subnet(self.tenant_id) - subnetnum
        for n in xrange(max):
            try:
                self.subnets.append(
                    self._create_subnet(self.networks[0],
                                        namestart='subnet-quotatest-'))
            except exc.NeutronClientException as e:
                if (e.status_code != 409):
                    raise
                hit_limit = True
                break
        self.assertFalse(hit_limit, "Failed: Hit quota limit !")

        try:
            self.subnets.append(
                self._create_subnet(self.networks[0],
                                    namestart='subnet-quotatest-'))
        except exc.NeutronClientException as e:
            if (e.status_code != 409):
                raise
            hit_limit = True
        self.assertTrue(hit_limit, "Failed: Did not hit quota limit !")

    @services('network')
    def test_create_ports_until_quota_hit(self):
        if not self.networks:
            self.networks.append(
                self._create_network(self.tenant_id,
                                     namestart='network-quotatest-'))
        hit_limit = False
        portnum = self._get_tenant_own_port_num(self.tenant_id)
        max = self._show_quota_port(self.tenant_id) - portnum
        for n in xrange(max):
            try:
                self.ports.append(
                    self._create_port(self.networks[0],
                                      namestart='port-quotatest-'))
            except exc.NeutronClientException as e:
                if (e.status_code != 409):
                    raise
                hit_limit = True
                break
        self.assertFalse(hit_limit, "Failed: Hit quota limit !")

        try:
            self.ports.append(
                self._create_port(self.networks[0],
                                  namestart='port-quotatest-'))
        except exc.NeutronClientException as e:
            if (e.status_code != 409):
                raise
            hit_limit = True
        self.assertTrue(hit_limit, "Failed: Did not hit quota limit !")
