# Copyright 2013 OpenStack Foundation
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

import uuid

from tempest.api.network import base_security_groups as base
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class NegativeSecGroupTest(base.BaseSecGroupTest):
    _interface = 'json'
    _tenant_network_cidr = CONF.network.tenant_network_cidr

    @classmethod
    def resource_setup(cls):
        super(NegativeSecGroupTest, cls).resource_setup()
        if not test.is_extension_enabled('security-group', 'network'):
            msg = "security-group extension not enabled."
            raise cls.skipException(msg)

    @test.attr(type=['negative', 'gate'])
    def test_show_non_existent_security_group(self):
        non_exist_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound, self.client.show_security_group,
                          non_exist_id)

    @test.attr(type=['negative', 'gate'])
    def test_show_non_existent_security_group_rule(self):
        non_exist_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound,
                          self.client.show_security_group_rule,
                          non_exist_id)

    @test.attr(type=['negative', 'gate'])
    def test_delete_non_existent_security_group(self):
        non_exist_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_security_group,
                          non_exist_id
                          )

    @test.attr(type=['negative', 'gate'])
    def test_create_security_group_rule_with_bad_protocol(self):
        group_create_body, _ = self._create_security_group()

        # Create rule with bad protocol name
        pname = 'bad_protocol_name'
        self.assertRaises(
            exceptions.BadRequest, self.client.create_security_group_rule,
            security_group_id=group_create_body['security_group']['id'],
            protocol=pname, direction='ingress', ethertype=self.ethertype)

    @test.attr(type=['negative', 'gate'])
    def test_create_security_group_rule_with_bad_remote_ip_prefix(self):
        group_create_body, _ = self._create_security_group()

        # Create rule with bad remote_ip_prefix
        prefix = ['192.168.1./24', '192.168.1.1/33', 'bad_prefix', '256']
        for remote_ip_prefix in prefix:
            self.assertRaises(
                exceptions.BadRequest, self.client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='tcp', direction='ingress', ethertype=self.ethertype,
                remote_ip_prefix=remote_ip_prefix)

    @test.attr(type=['negative', 'gate'])
    def test_create_security_group_rule_with_non_existent_remote_groupid(self):
        group_create_body, _ = self._create_security_group()
        non_exist_id = str(uuid.uuid4())

        # Create rule with non existent remote_group_id
        group_ids = ['bad_group_id', non_exist_id]
        for remote_group_id in group_ids:
            self.assertRaises(
                exceptions.NotFound, self.client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='tcp', direction='ingress', ethertype=self.ethertype,
                remote_group_id=remote_group_id)

    @test.attr(type=['negative', 'gate'])
    def test_create_security_group_rule_with_remote_ip_and_group(self):
        sg1_body, _ = self._create_security_group()
        sg2_body, _ = self._create_security_group()

        # Create rule specifying both remote_ip_prefix and remote_group_id
        prefix = self._tenant_network_cidr
        self.assertRaises(
            exceptions.BadRequest, self.client.create_security_group_rule,
            security_group_id=sg1_body['security_group']['id'],
            protocol='tcp', direction='ingress',
            ethertype=self.ethertype, remote_ip_prefix=prefix,
            remote_group_id=sg2_body['security_group']['id'])

    @test.attr(type=['negative', 'gate'])
    def test_create_security_group_rule_with_bad_ethertype(self):
        group_create_body, _ = self._create_security_group()

        # Create rule with bad ethertype
        ethertype = 'bad_ethertype'
        self.assertRaises(
            exceptions.BadRequest, self.client.create_security_group_rule,
            security_group_id=group_create_body['security_group']['id'],
            protocol='udp', direction='ingress', ethertype=ethertype)

    @test.attr(type=['negative', 'gate'])
    def test_create_security_group_rule_with_invalid_ports(self):
        group_create_body, _ = self._create_security_group()

        # Create rule for tcp protocol with invalid ports
        states = [(-16, 80, 'Invalid value for port -16'),
                  (80, 79, 'port_range_min must be <= port_range_max'),
                  (80, 65536, 'Invalid value for port 65536'),
                  (None, 6, 'port_range_min must be <= port_range_max'),
                  (-16, 65536, 'Invalid value for port')]
        for pmin, pmax, msg in states:
            ex = self.assertRaises(
                exceptions.BadRequest, self.client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='tcp', port_range_min=pmin, port_range_max=pmax,
                direction='ingress', ethertype=self.ethertype)
            self.assertIn(msg, str(ex))

        # Create rule for icmp protocol with invalid ports
        states = [(1, 256, 'Invalid value for ICMP code'),
                  (None, 6, 'ICMP type (port-range-min) is missing'),
                  (300, 1, 'Invalid value for ICMP type')]
        for pmin, pmax, msg in states:
            ex = self.assertRaises(
                exceptions.BadRequest, self.client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='icmp', port_range_min=pmin, port_range_max=pmax,
                direction='ingress', ethertype=self.ethertype)
            self.assertIn(msg, str(ex))

    @test.attr(type=['negative', 'smoke'])
    def test_create_additional_default_security_group_fails(self):
        # Create security group named 'default', it should be failed.
        name = 'default'
        self.assertRaises(exceptions.Conflict,
                          self.client.create_security_group,
                          name=name)

    @test.attr(type=['negative', 'smoke'])
    def test_create_duplicate_security_group_rule_fails(self):
        # Create duplicate security group rule, it should fail.
        body, _ = self._create_security_group()

        min_port = 66
        max_port = 67
        # Create a rule with valid params
        resp, _ = self.client.create_security_group_rule(
            security_group_id=body['security_group']['id'],
            direction='ingress',
            ethertype=self.ethertype,
            protocol='tcp',
            port_range_min=min_port,
            port_range_max=max_port
        )

        # Try creating the same security group rule, it should fail
        self.assertRaises(
            exceptions.Conflict, self.client.create_security_group_rule,
            security_group_id=body['security_group']['id'],
            protocol='tcp', direction='ingress', ethertype=self.ethertype,
            port_range_min=min_port, port_range_max=max_port)

    @test.attr(type=['negative', 'smoke'])
    def test_create_security_group_rule_with_non_existent_security_group(self):
        # Create security group rules with not existing security group.
        non_existent_sg = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound,
                          self.client.create_security_group_rule,
                          security_group_id=non_existent_sg,
                          direction='ingress', ethertype=self.ethertype)


class NegativeSecGroupIPv6Test(NegativeSecGroupTest):
    _ip_version = 6
    _tenant_network_cidr = CONF.network.tenant_network_v6_cidr

    @test.attr(type=['negative', 'gate'])
    def test_create_security_group_rule_wrong_ip_prefix_version(self):
        group_create_body, _ = self._create_security_group()

        # Create rule with bad remote_ip_prefix
        pairs = ({'ethertype': 'IPv6',
                  'ip_prefix': CONF.network.tenant_network_cidr},
                 {'ethertype': 'IPv4',
                  'ip_prefix': CONF.network.tenant_network_v6_cidr})
        for pair in pairs:
            self.assertRaisesRegexp(
                exceptions.BadRequest,
                "Conflicting value ethertype",
                self.client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='tcp', direction='ingress',
                ethertype=pair['ethertype'],
                remote_ip_prefix=pair['ip_prefix'])
