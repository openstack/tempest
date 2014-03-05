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

from tempest.api.compute.security_groups import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


def not_existing_id():
    if CONF.service_available.neutron:
        return data_utils.rand_uuid()
    else:
        return data_utils.rand_int_id(start=999)


class SecurityGroupRulesNegativeTestJSON(base.BaseSecurityGroupsTest):

    @classmethod
    def setUpClass(cls):
        super(SecurityGroupRulesNegativeTestJSON, cls).setUpClass()
        cls.client = cls.security_groups_client

    @test.attr(type=['negative', 'smoke'])
    def test_create_security_group_rule_with_non_existent_id(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with non existent Parent group id
        # Adding rules to the non existent Security Group id
        parent_group_id = not_existing_id()
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        self.assertRaises(exceptions.NotFound,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    def test_create_security_group_rule_with_invalid_id(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with Parent group id which is not integer
        # Adding rules to the non int Security Group id
        parent_group_id = data_utils.rand_name('non_int_id')
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    def test_create_security_group_rule_duplicate(self):
        # Negative test: Create Security Group rule duplicate should fail
        # Creating a Security Group to add rule to it
        resp, sg = self.create_security_group()
        # Adding rules to the created Security Group
        parent_group_id = sg['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22

        resp, rule = \
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol,
                                                   from_port,
                                                   to_port)
        self.addCleanup(self.client.delete_security_group_rule, rule['id'])
        self.assertEqual(200, resp.status)
        # Add the same rule to the group should fail
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    def test_create_security_group_rule_with_invalid_ip_protocol(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid ip_protocol
        # Creating a Security Group to add rule to it
        resp, sg = self.create_security_group()
        # Adding rules to the created Security Group
        parent_group_id = sg['id']
        ip_protocol = data_utils.rand_name('999')
        from_port = 22
        to_port = 22

        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    def test_create_security_group_rule_with_invalid_from_port(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid from_port
        # Creating a Security Group to add rule to it
        resp, sg = self.create_security_group()
        # Adding rules to the created Security Group
        parent_group_id = sg['id']
        ip_protocol = 'tcp'
        from_port = data_utils.rand_int_id(start=65536)
        to_port = 22
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    def test_create_security_group_rule_with_invalid_to_port(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid to_port
        # Creating a Security Group to add rule to it
        resp, sg = self.create_security_group()
        # Adding rules to the created Security Group
        parent_group_id = sg['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = data_utils.rand_int_id(start=65536)
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    def test_create_security_group_rule_with_invalid_port_range(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid port range.
        # Creating a Security Group to add rule to it.
        resp, sg = self.create_security_group()
        # Adding a rule to the created Security Group
        secgroup_id = sg['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 21
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          secgroup_id, ip_protocol, from_port, to_port)

    @test.attr(type=['negative', 'smoke'])
    def test_delete_security_group_rule_with_non_existent_id(self):
        # Negative test: Deletion of Security Group rule should be FAIL
        # with non existent id
        non_existent_rule_id = not_existing_id()
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_security_group_rule,
                          non_existent_rule_id)


class SecurityGroupRulesNegativeTestXML(SecurityGroupRulesNegativeTestJSON):
    _interface = 'xml'
