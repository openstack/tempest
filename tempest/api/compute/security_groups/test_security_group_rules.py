# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from tempest.api.compute import base
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class SecurityGroupRulesTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(SecurityGroupRulesTestJSON, cls).setUpClass()
        cls.client = cls.security_groups_client

    @attr(type=['positive', 'gate'])
    def test_security_group_rules_create(self):
        # Positive test: Creation of Security Group rule
        # should be successfull
        #Creating a Security Group to add rules to it
        s_name = rand_name('securitygroup-')
        s_description = rand_name('description-')
        resp, securitygroup = \
            self.client.create_security_group(s_name, s_description)
        securitygroup_id = securitygroup['id']
        self.addCleanup(self.client.delete_security_group, securitygroup_id)
        #Adding rules to the created Security Group
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        resp, rule = \
            self.client.create_security_group_rule(securitygroup_id,
                                                   ip_protocol,
                                                   from_port,
                                                   to_port)
        self.addCleanup(self.client.delete_security_group_rule, rule['id'])
        self.assertEqual(200, resp.status)

    @attr(type=['positive', 'gate'])
    def test_security_group_rules_create_with_optional_arguments(self):
        # Positive test: Creation of Security Group rule
        # with optional arguments
        # should be successfull

        secgroup1 = None
        secgroup2 = None
        #Creating a Security Group to add rules to it
        s_name = rand_name('securitygroup-')
        s_description = rand_name('description-')
        resp, securitygroup = \
            self.client.create_security_group(s_name, s_description)
        secgroup1 = securitygroup['id']
        self.addCleanup(self.client.delete_security_group, secgroup1)
        #Creating a Security Group so as to assign group_id to the rule
        s_name2 = rand_name('securitygroup-')
        s_description2 = rand_name('description-')
        resp, securitygroup = \
            self.client.create_security_group(s_name2, s_description2)
        secgroup2 = securitygroup['id']
        self.addCleanup(self.client.delete_security_group, secgroup2)
        #Adding rules to the created Security Group with optional arguments
        parent_group_id = secgroup1
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        cidr = '10.2.3.124/24'
        group_id = secgroup2
        resp, rule = \
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol,
                                                   from_port,
                                                   to_port,
                                                   cidr=cidr,
                                                   group_id=group_id)
        self.addCleanup(self.client.delete_security_group_rule, rule['id'])
        self.assertEqual(200, resp.status)

    @attr(type=['negative', 'gate'])
    def test_security_group_rules_create_with_invalid_id(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid Parent group id
        # Adding rules to the invalid Security Group id
        parent_group_id = rand_name('999')
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        self.assertRaises(exceptions.NotFound,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @attr(type=['negative', 'gate'])
    def test_security_group_rules_create_with_invalid_ip_protocol(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid ip_protocol
        #Creating a Security Group to add rule to it
        s_name = rand_name('securitygroup-')
        s_description = rand_name('description-')
        resp, securitygroup = self.client.create_security_group(s_name,
                                                                s_description)
        #Adding rules to the created Security Group
        parent_group_id = securitygroup['id']
        ip_protocol = rand_name('999')
        from_port = 22
        to_port = 22

        self.addCleanup(self.client.delete_security_group, securitygroup['id'])
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @attr(type=['negative', 'gate'])
    def test_security_group_rules_create_with_invalid_from_port(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid from_port
        #Creating a Security Group to add rule to it
        s_name = rand_name('securitygroup-')
        s_description = rand_name('description-')
        resp, securitygroup = self.client.create_security_group(s_name,
                                                                s_description)
        #Adding rules to the created Security Group
        parent_group_id = securitygroup['id']
        ip_protocol = 'tcp'
        from_port = rand_name('999')
        to_port = 22
        self.addCleanup(self.client.delete_security_group, securitygroup['id'])
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @attr(type=['negative', 'gate'])
    def test_security_group_rules_create_with_invalid_to_port(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid from_port
        #Creating a Security Group to add rule to it
        s_name = rand_name('securitygroup-')
        s_description = rand_name('description-')
        resp, securitygroup = self.client.create_security_group(s_name,
                                                                s_description)
        #Adding rules to the created Security Group
        parent_group_id = securitygroup['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = rand_name('999')
        self.addCleanup(self.client.delete_security_group, securitygroup['id'])
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          parent_group_id, ip_protocol, from_port, to_port)

    @attr(type=['negative', 'gate'])
    def test_security_group_rules_create_with_invalid_port_range(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid port range.
        # Creating a Security Group to add rule to it.
        s_name = rand_name('securitygroup-')
        s_description = rand_name('description-')
        resp, securitygroup = self.client.create_security_group(s_name,
                                                                s_description)
        # Adding a rule to the created Security Group
        secgroup_id = securitygroup['id']
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 21
        self.addCleanup(self.client.delete_security_group, securitygroup['id'])
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group_rule,
                          secgroup_id, ip_protocol, from_port, to_port)

    @attr(type=['negative', 'gate'])
    def test_security_group_rules_delete_with_invalid_id(self):
        # Negative test: Deletion of Security Group rule should be FAIL
        # with invalid rule id
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_security_group_rule,
                          rand_name('999'))

    @attr(type=['positive', 'gate'])
    def test_security_group_rules_list(self):
        # Positive test: Created Security Group rules should be
        # in the list of all rules
        # Creating a Security Group to add rules to it
        s_name = rand_name('securitygroup-')
        s_description = rand_name('description-')
        resp, securitygroup = \
            self.client.create_security_group(s_name, s_description)
        securitygroup_id = securitygroup['id']
        # Delete the Security Group at the end of this method
        self.addCleanup(self.client.delete_security_group, securitygroup_id)

        # Add a first rule to the created Security Group
        ip_protocol1 = 'tcp'
        from_port1 = 22
        to_port1 = 22
        resp, rule = \
            self.client.create_security_group_rule(securitygroup_id,
                                                   ip_protocol1,
                                                   from_port1, to_port1)
        rule1_id = rule['id']
        # Delete the Security Group rule1 at the end of this method
        self.addCleanup(self.client.delete_security_group_rule, rule1_id)

        # Add a second rule to the created Security Group
        ip_protocol2 = 'icmp'
        from_port2 = -1
        to_port2 = -1
        resp, rule = \
            self.client.create_security_group_rule(securitygroup_id,
                                                   ip_protocol2,
                                                   from_port2, to_port2)
        rule2_id = rule['id']
        # Delete the Security Group rule2 at the end of this method
        self.addCleanup(self.client.delete_security_group_rule, rule2_id)

        # Get rules of the created Security Group
        resp, rules = \
            self.client.list_security_group_rules(securitygroup_id)
        self.assertTrue(any([i for i in rules if i['id'] == rule1_id]))
        self.assertTrue(any([i for i in rules if i['id'] == rule2_id]))


class SecurityGroupRulesTestXML(SecurityGroupRulesTestJSON):
    _interface = 'xml'
