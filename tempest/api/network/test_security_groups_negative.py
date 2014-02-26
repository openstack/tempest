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
from tempest import exceptions
from tempest import test


class NegativeSecGroupTest(base.BaseSecGroupTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(NegativeSecGroupTest, cls).setUpClass()
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

        #Create rule with bad protocol name
        pname = 'bad_protocol_name'
        self.assertRaises(
            exceptions.BadRequest, self.client.create_security_group_rule,
            security_group_id=group_create_body['security_group']['id'],
            protocol=pname, direction='ingress')

    @test.attr(type=['negative', 'gate'])
    def test_create_security_group_rule_with_invalid_ports(self):
        group_create_body, _ = self._create_security_group()

        #Create rule with invalid ports
        states = [(-16, 80, 'Invalid value for port -16'),
                  (80, 79, 'port_range_min must be <= port_range_max'),
                  (80, 65536, 'Invalid value for port 65536'),
                  (-16, 65536, 'Invalid value for port')]
        for pmin, pmax, msg in states:
            ex = self.assertRaises(
                exceptions.BadRequest, self.client.create_security_group_rule,
                security_group_id=group_create_body['security_group']['id'],
                protocol='tcp', port_range_min=pmin, port_range_max=pmax,
                direction='ingress')
            self.assertIn(msg, str(ex))

    @test.attr(type=['negative', 'smoke'])
    def test_create_additional_default_security_group_fails(self):
        # Create security group named 'default', it should be failed.
        name = 'default'
        self.assertRaises(exceptions.Conflict,
                          self.client.create_security_group,
                          name=name)

    @test.attr(type=['negative', 'smoke'])
    def test_create_security_group_rule_with_non_existent_security_group(self):
        # Create security group rules with not existing security group.
        non_existent_sg = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound,
                          self.client.create_security_group_rule,
                          security_group_id=non_existent_sg,
                          direction='ingress')


class NegativeSecGroupTestXML(NegativeSecGroupTest):
    _interface = 'xml'
