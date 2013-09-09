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

MAX_REASONABLE_ITERATIONS = 51  # more than enough. Default for port is 50.


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

    def test_create_network_until_quota_hit(self):
        hit_limit = False
        for n in xrange(MAX_REASONABLE_ITERATIONS):
            try:
                self.networks.append(
                    self._create_network(self.tenant_id,
                                         namestart='network-quotatest-'))
            except exc.NeutronClientException as e:
                if (e.status_code != 409):
                    raise
                hit_limit = True
                break
        self.assertTrue(hit_limit, "Failed: Did not hit quota limit !")

    def test_create_subnet_until_quota_hit(self):
        if not self.networks:
            self.networks.append(
                self._create_network(self.tenant_id,
                                     namestart='network-quotatest-'))
        hit_limit = False
        for n in xrange(MAX_REASONABLE_ITERATIONS):
            try:
                self.subnets.append(
                    self._create_subnet(self.networks[0],
                                        namestart='subnet-quotatest-'))
            except exc.NeutronClientException as e:
                if (e.status_code != 409):
                    raise
                hit_limit = True
                break
        self.assertTrue(hit_limit, "Failed: Did not hit quota limit !")

    def test_create_ports_until_quota_hit(self):
        if not self.networks:
            self.networks.append(
                self._create_network(self.tenant_id,
                                     namestart='network-quotatest-'))
        hit_limit = False
        for n in xrange(MAX_REASONABLE_ITERATIONS):
            try:
                self.ports.append(
                    self._create_port(self.networks[0],
                                      namestart='port-quotatest-'))
            except exc.NeutronClientException as e:
                if (e.status_code != 409):
                    raise
                hit_limit = True
                break
        self.assertTrue(hit_limit, "Failed: Did not hit quota limit !")
