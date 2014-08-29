# Copyright 2014 NEC Corporation.  All rights reserved.
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

import testtools

from tempest.api.compute import base
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class SecurityGroupDefaultRulesTest(base.BaseV2ComputeAdminTest):

    @classmethod
    # TODO(GMann): Once Bug# 1311500 is fixed, these test can run
    # for Neutron also.
    @testtools.skipIf(CONF.service_available.neutron,
                      "Skip as this functionality is not yet "
                      "implemented in Neutron. Related Bug#1311500")
    @test.safe_setup
    def setUpClass(cls):
        # A network and a subnet will be created for these tests
        cls.set_network_resources(network=True, subnet=True)
        super(SecurityGroupDefaultRulesTest, cls).setUpClass()
        cls.adm_client = cls.os_adm.security_group_default_rules_client

    def _create_security_group_default_rules(self, ip_protocol='tcp',
                                             from_port=22, to_port=22,
                                             cidr='10.10.0.0/24'):
        # Create Security Group default rule
        _, rule = self.adm_client.create_security_default_group_rule(
            ip_protocol,
            from_port,
            to_port,
            cidr=cidr)
        self.assertEqual(ip_protocol, rule['ip_protocol'])
        self.assertEqual(from_port, rule['from_port'])
        self.assertEqual(to_port, rule['to_port'])
        self.assertEqual(cidr, rule['ip_range']['cidr'])
        return rule

    @test.attr(type='smoke')
    def test_create_delete_security_group_default_rules(self):
        # Create and delete Security Group default rule
        ip_protocols = ['tcp', 'udp', 'icmp']
        for ip_protocol in ip_protocols:
            rule = self._create_security_group_default_rules(ip_protocol)
            # Delete Security Group default rule
            self.adm_client.delete_security_group_default_rule(rule['id'])
            self.assertRaises(exceptions.NotFound,
                              self.adm_client.get_security_group_default_rule,
                              rule['id'])

    @test.attr(type='smoke')
    def test_create_security_group_default_rule_without_cidr(self):
        ip_protocol = 'udp'
        from_port = 80
        to_port = 80
        _, rule = self.adm_client.create_security_default_group_rule(
            ip_protocol,
            from_port,
            to_port)
        self.addCleanup(self.adm_client.delete_security_group_default_rule,
                        rule['id'])
        self.assertNotEqual(0, rule['id'])
        self.assertEqual('0.0.0.0/0', rule['ip_range']['cidr'])

    @test.attr(type='smoke')
    def test_create_security_group_default_rule_with_blank_cidr(self):
        ip_protocol = 'icmp'
        from_port = 10
        to_port = 10
        cidr = ''
        _, rule = self.adm_client.create_security_default_group_rule(
            ip_protocol,
            from_port,
            to_port,
            cidr=cidr)
        self.addCleanup(self.adm_client.delete_security_group_default_rule,
                        rule['id'])
        self.assertNotEqual(0, rule['id'])
        self.assertEqual('0.0.0.0/0', rule['ip_range']['cidr'])

    @test.attr(type='smoke')
    def test_security_group_default_rules_list(self):
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        cidr = '10.10.0.0/24'
        rule = self._create_security_group_default_rules(ip_protocol,
                                                         from_port,
                                                         to_port,
                                                         cidr)
        self.addCleanup(self.adm_client.delete_security_group_default_rule,
                        rule['id'])
        _, rules = self.adm_client.list_security_group_default_rules()
        self.assertNotEqual(0, len(rules))
        self.assertIn(rule, rules)

    @test.attr(type='smoke')
    def test_default_security_group_default_rule_show(self):
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        cidr = '10.10.0.0/24'
        rule = self._create_security_group_default_rules(ip_protocol,
                                                         from_port,
                                                         to_port,
                                                         cidr)
        self.addCleanup(self.adm_client.delete_security_group_default_rule,
                        rule['id'])
        _, fetched_rule = self.adm_client.get_security_group_default_rule(
            rule['id'])
        self.assertEqual(rule, fetched_rule)
