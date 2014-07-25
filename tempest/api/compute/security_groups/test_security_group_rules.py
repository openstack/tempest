# Copyright 2012 OpenStack Foundation
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
from tempest import config
from tempest import test

CONF = config.CONF


class SecurityGroupRulesTestJSON(base.BaseSecurityGroupsTest):

    @classmethod
    def setUpClass(cls):
        super(SecurityGroupRulesTestJSON, cls).setUpClass()
        cls.client = cls.security_groups_client
        cls.neutron_available = CONF.service_available.neutron

    @test.attr(type='smoke')
    @test.services('network')
    def test_security_group_rules_create(self):
        # Positive test: Creation of Security Group rule
        # should be successful
        # Creating a Security Group to add rules to it
        resp, security_group = self.create_security_group()
        securitygroup_id = security_group['id']
        # Adding rules to the created Security Group
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

    @test.attr(type='smoke')
    @test.services('network')
    def test_security_group_rules_create_with_optional_arguments(self):
        # Positive test: Creation of Security Group rule
        # with optional arguments
        # should be successful

        secgroup1 = None
        secgroup2 = None
        # Creating a Security Group to add rules to it
        resp, security_group = self.create_security_group()
        secgroup1 = security_group['id']
        # Creating a Security Group so as to assign group_id to the rule
        resp, security_group = self.create_security_group()
        secgroup2 = security_group['id']
        # Adding rules to the created Security Group with optional arguments
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
        self.assertEqual(200, resp.status)

    @test.attr(type='smoke')
    @test.services('network')
    def test_security_group_rules_list(self):
        # Positive test: Created Security Group rules should be
        # in the list of all rules
        # Creating a Security Group to add rules to it
        resp, security_group = self.create_security_group()
        securitygroup_id = security_group['id']

        # Add a first rule to the created Security Group
        ip_protocol1 = 'tcp'
        from_port1 = 22
        to_port1 = 22
        resp, rule = \
            self.client.create_security_group_rule(securitygroup_id,
                                                   ip_protocol1,
                                                   from_port1, to_port1)
        rule1_id = rule['id']

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

    @test.attr(type='smoke')
    @test.services('network')
    def test_security_group_rules_delete_when_peer_group_deleted(self):
        # Positive test:rule will delete when peer group deleting
        # Creating a Security Group to add rules to it
        resp, security_group = self.create_security_group()
        sg1_id = security_group['id']
        # Creating other Security Group to access to group1
        resp, security_group = self.create_security_group()
        sg2_id = security_group['id']
        # Adding rules to the Group1
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        resp, rule = \
            self.client.create_security_group_rule(sg1_id,
                                                   ip_protocol,
                                                   from_port,
                                                   to_port,
                                                   group_id=sg2_id)

        self.assertEqual(200, resp.status)
        # Delete group2
        resp, body = self.client.delete_security_group(sg2_id)
        self.assertEqual(202, resp.status)
        # Get rules of the Group1
        resp, rules = \
            self.client.list_security_group_rules(sg1_id)
        # The group1 has no rules because group2 has deleted
        self.assertEqual(0, len(rules))


class SecurityGroupRulesTestXML(SecurityGroupRulesTestJSON):
    _interface = 'xml'
