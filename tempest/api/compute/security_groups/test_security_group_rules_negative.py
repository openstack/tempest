# Copyright 2013 Huawei Technologies Co.,LTD.
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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute.security_groups import base
from tempest import config
from tempest import test

CONF = config.CONF


def not_existing_id():
    if CONF.service_available.neutron:
        return data_utils.rand_uuid()
    else:
        return data_utils.rand_int_id(start=999)


class SecurityGroupRulesNegativeTestJSON(base.BaseSecurityGroupsTest):

    @classmethod
    def setup_clients(cls):
        super(SecurityGroupRulesNegativeTestJSON, cls).setup_clients()
        cls.client = cls.security_groups_client

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('1d507e98-7951-469b-82c3-23f1e6b8c254')
    @test.services('network')
    def test_create_security_group_rule_with_non_existent_id(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with non existent Parent group id
        # Adding rules to the non existent Security Group id
        parent_group_id = not_existing_id()
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        self.assertRaises(lib_exc.NotFound,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('2244d7e4-adb7-4ecb-9930-2d77e123ce4f')
    @test.services('network')
    def test_create_security_group_rule_with_invalid_id(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with Parent group id which is not integer
        # Adding rules to the non int Security Group id
        parent_group_id = data_utils.rand_name('non_int_id')
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('8bd56d02-3ffa-4d67-9933-b6b9a01d6089')
    @test.services('network')
    def test_create_security_group_rule_duplicate(self):
        # Negative test: Create Security Group rule duplicate should fail
        # Creating a Security Group to add rule to it
        sg = self.create_security_group()
        # Adding rules to the created Security Group
        parent_group_id = sg['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22

        rule = \
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol,
                                                   from_port,
                                                   to_port)
        self.addCleanup(self.client.delete_security_group_rule, rule['id'])
        # Add the same rule to the group should fail
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('84c81249-9f6e-439c-9bbf-cbb0d2cddbdf')
    @test.services('network')
    def test_create_security_group_rule_with_invalid_ip_protocol(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid ip_protocol
        # Creating a Security Group to add rule to it
        sg = self.create_security_group()
        # Adding rules to the created Security Group
        parent_group_id = sg['id']
        ip_protocol = data_utils.rand_name('999')
        from_port = 22
        to_port = 22

        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('12bbc875-1045-4f7a-be46-751277baedb9')
    @test.services('network')
    def test_create_security_group_rule_with_invalid_from_port(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid from_port
        # Creating a Security Group to add rule to it
        sg = self.create_security_group()
        # Adding rules to the created Security Group
        parent_group_id = sg['id']
        ip_protocol = 'tcp'
        from_port = data_utils.rand_int_id(start=65536)
        to_port = 22
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('ff88804d-144f-45d1-bf59-dd155838a43a')
    @test.services('network')
    def test_create_security_group_rule_with_invalid_to_port(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid to_port
        # Creating a Security Group to add rule to it
        sg = self.create_security_group()
        # Adding rules to the created Security Group
        parent_group_id = sg['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = data_utils.rand_int_id(start=65536)
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('00296fa9-0576-496a-ae15-fbab843189e0')
    @test.services('network')
    def test_create_security_group_rule_with_invalid_port_range(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid port range.
        # Creating a Security Group to add rule to it.
        sg = self.create_security_group()
        # Adding a rule to the created Security Group
        secgroup_id = sg['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 21
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group_rule,
                          secgroup_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('56fddcca-dbb8-4494-a0db-96e9f869527c')
    @test.services('network')
    def test_delete_security_group_rule_with_non_existent_id(self):
        # Negative test: Deletion of Security Group rule should be FAIL
        # with non existent id
        non_existent_rule_id = not_existing_id()
        self.assertRaises(lib_exc.NotFound,
                          self.client.delete_security_group_rule,
                          non_existent_rule_id)
