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

from tempest.api.network import base_security_groups as base
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class NegativeSecGroupTest(base.BaseSecGroupTest):

    @classmethod
    def skip_checks(cls):
        super(NegativeSecGroupTest, cls).skip_checks()
        if not utils.is_extension_enabled('security-group', 'network'):
            msg = "security-group extension not enabled."
            raise cls.skipException(msg)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('424fd5c3-9ddc-486a-b45f-39bf0c820fc6')
    def test_show_non_existent_security_group(self):
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(
            lib_exc.NotFound, self.security_groups_client.show_security_group,
            non_exist_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('4c094c09-000b-4e41-8100-9617600c02a6')
    def test_show_non_existent_security_group_rule(self):
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(
            lib_exc.NotFound,
            self.security_group_rules_client.show_security_group_rule,
            non_exist_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('1f1bb89d-5664-4956-9fcd-83ee0fa603df')
    def test_delete_non_existent_security_group(self):
        non_exist_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound,
                          self.security_groups_client.delete_security_group,
                          non_exist_id
                          )

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('981bdc22-ce48-41ed-900a-73148b583958')
    def test_create_security_group_rule_with_bad_protocol(self):
        group_create_body, _ = self._create_security_group()

        # Create rule with bad protocol name
        pname = 'bad_protocol_name'
        self.assertRaises(
            lib_exc.BadRequest,
            self.security_group_rules_client.create_security_group_rule,
            security_group_id=group_create_body['security_group']['id'],
            protocol=pname, direction='ingress', ethertype=self.ethertype)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5f8daf69-3c5f-4aaa-88c9-db1d66f68679')
    def test_create_security_group_rule_with_bad_remote_ip_prefix(self):
        group_create_body, _ = self._create_security_group()

        # Create rule with bad remote_ip_prefix
        prefix = ['192.168.1./24', '192.168.1.1/33', 'bad_prefix', '256']
        for remote_ip_prefix in prefix:
            self.assertRaises(
                lib_exc.BadRequest,
                self.security_group_rules_client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='tcp', direction='ingress', ethertype=self.ethertype,
                remote_ip_prefix=remote_ip_prefix)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('4bf786fd-2f02-443c-9716-5b98e159a49a')
    def test_create_security_group_rule_with_non_existent_remote_groupid(self):
        group_create_body, _ = self._create_security_group()
        non_exist_id = data_utils.rand_uuid()

        # Create rule with non existent remote_group_id
        group_ids = ['bad_group_id', non_exist_id]
        for remote_group_id in group_ids:
            self.assertRaises(
                lib_exc.NotFound,
                self.security_group_rules_client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='tcp', direction='ingress', ethertype=self.ethertype,
                remote_group_id=remote_group_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b5c4b247-6b02-435b-b088-d10d45650881')
    def test_create_security_group_rule_with_remote_ip_and_group(self):
        sg1_body, _ = self._create_security_group()
        sg2_body, _ = self._create_security_group()

        # Create rule specifying both remote_ip_prefix and remote_group_id
        prefix = str(self.cidr)
        self.assertRaises(
            lib_exc.BadRequest,
            self.security_group_rules_client.create_security_group_rule,
            security_group_id=sg1_body['security_group']['id'],
            protocol='tcp', direction='ingress',
            ethertype=self.ethertype, remote_ip_prefix=prefix,
            remote_group_id=sg2_body['security_group']['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5666968c-fff3-40d6-9efc-df1c8bd01abb')
    def test_create_security_group_rule_with_bad_ethertype(self):
        group_create_body, _ = self._create_security_group()

        # Create rule with bad ethertype
        ethertype = 'bad_ethertype'
        self.assertRaises(
            lib_exc.BadRequest,
            self.security_group_rules_client.create_security_group_rule,
            security_group_id=group_create_body['security_group']['id'],
            protocol='udp', direction='ingress', ethertype=ethertype)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0d9c7791-f2ad-4e2f-ac73-abf2373b0d2d')
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
                lib_exc.BadRequest,
                self.security_group_rules_client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='tcp', port_range_min=pmin, port_range_max=pmax,
                direction='ingress', ethertype=self.ethertype)
            self.assertIn(msg, str(ex))

        # Create rule for icmp protocol with invalid ports
        states = [(1, 256, 'Invalid value for ICMP code'),
                  (-1, 25, 'Invalid value'),
                  (None, 6, 'ICMP type (port-range-min) is missing'),
                  (300, 1, 'Invalid value for ICMP type')]
        for pmin, pmax, msg in states:
            ex = self.assertRaises(
                lib_exc.BadRequest,
                self.security_group_rules_client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='icmp', port_range_min=pmin, port_range_max=pmax,
                direction='ingress', ethertype=self.ethertype)
            self.assertIn(msg, str(ex))

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('2323061e-9fbf-4eb0-b547-7e8fafc90849')
    def test_create_additional_default_security_group_fails(self):
        # Create security group named 'default', it should be failed.
        name = 'default'
        self.assertRaises(lib_exc.Conflict,
                          self.security_groups_client.create_security_group,
                          name=name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('966e2b96-023a-11e7-a9e4-fa163e4fa634')
    def test_create_security_group_update_name_default(self):
        # Update security group name to 'default', it should be failed.
        group_create_body, _ = self._create_security_group()
        self.assertRaises(lib_exc.Conflict,
                          self.security_groups_client.update_security_group,
                          group_create_body['security_group']['id'],
                          name="default")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8fde898f-ce88-493b-adc9-4e4692879fc5')
    def test_create_duplicate_security_group_rule_fails(self):
        # Create duplicate security group rule, it should fail.
        body, _ = self._create_security_group()

        min_port = 66
        max_port = 67
        # Create a rule with valid params
        self.security_group_rules_client.create_security_group_rule(
            security_group_id=body['security_group']['id'],
            direction='ingress',
            ethertype=self.ethertype,
            protocol='tcp',
            port_range_min=min_port,
            port_range_max=max_port
        )

        # Try creating the same security group rule, it should fail
        self.assertRaises(
            lib_exc.Conflict,
            self.security_group_rules_client.create_security_group_rule,
            security_group_id=body['security_group']['id'],
            protocol='tcp', direction='ingress', ethertype=self.ethertype,
            port_range_min=min_port, port_range_max=max_port)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('be308db6-a7cf-4d5c-9baf-71bafd73f35e')
    def test_create_security_group_rule_with_non_existent_security_group(self):
        # Create security group rules with not existing security group.
        non_existent_sg = data_utils.rand_uuid()
        self.assertRaises(
            lib_exc.NotFound,
            self.security_group_rules_client.create_security_group_rule,
            security_group_id=non_existent_sg,
            direction='ingress', ethertype=self.ethertype)


class NegativeSecGroupIPv6Test(NegativeSecGroupTest):
    _ip_version = 6

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7607439c-af73-499e-bf64-f687fd12a842')
    def test_create_security_group_rule_wrong_ip_prefix_version(self):
        group_create_body, _ = self._create_security_group()

        # Create rule with bad remote_ip_prefix
        pairs = ({'ethertype': 'IPv6',
                  'ip_prefix': CONF.network.project_network_cidr},
                 {'ethertype': 'IPv4',
                  'ip_prefix': CONF.network.project_network_v6_cidr})
        for pair in pairs:
            self.assertRaisesRegex(
                lib_exc.BadRequest,
                "Conflicting value ethertype",
                self.security_group_rules_client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='tcp', direction='ingress',
                ethertype=pair['ethertype'],
                remote_ip_prefix=pair['ip_prefix'])
