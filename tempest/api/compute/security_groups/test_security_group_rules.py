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
from tempest.common.utils import data_utils
from tempest import config
from tempest.test import attr

CONF = config.CONF


class SecurityGroupRulesTestJSON(base.BaseSecurityGroupsTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(SecurityGroupRulesTestJSON, cls).setUpClass()
        cls.client = cls.security_groups_client
        cls.neutron_available = CONF.service_available.neutron

    @attr(type='smoke')
    def test_security_group_rules_create(self):
        # Positive test: Creation of Security Group rule
        # should be successful
        # Creating a Security Group to add rules to it
        s_name = data_utils.rand_name('securitygroup-')
        s_description = data_utils.rand_name('description-')
        resp, securitygroup = \
            self.client.create_security_group(s_name, s_description)
        securitygroup_id = securitygroup['id']
        self.addCleanup(self.client.delete_security_group, securitygroup_id)
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

    @attr(type='smoke')
    def test_security_group_rules_create_with_optional_arguments(self):
        # Positive test: Creation of Security Group rule
        # with optional arguments
        # should be successful

        secgroup1 = None
        secgroup2 = None
        # Creating a Security Group to add rules to it
        s_name = data_utils.rand_name('securitygroup-')
        s_description = data_utils.rand_name('description-')
        resp, securitygroup = \
            self.client.create_security_group(s_name, s_description)
        secgroup1 = securitygroup['id']
        self.addCleanup(self.client.delete_security_group, secgroup1)
        # Creating a Security Group so as to assign group_id to the rule
        s_name2 = data_utils.rand_name('securitygroup-')
        s_description2 = data_utils.rand_name('description-')
        resp, securitygroup = \
            self.client.create_security_group(s_name2, s_description2)
        secgroup2 = securitygroup['id']
        self.addCleanup(self.client.delete_security_group, secgroup2)
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
        self.addCleanup(self.client.delete_security_group_rule, rule['id'])
        self.assertEqual(200, resp.status)

    @attr(type='smoke')
    def test_security_group_rules_list(self):
        # Positive test: Created Security Group rules should be
        # in the list of all rules
        # Creating a Security Group to add rules to it
        s_name = data_utils.rand_name('securitygroup-')
        s_description = data_utils.rand_name('description-')
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

    @attr(type='smoke')
    def test_security_group_rules_delete_when_peer_group_deleted(self):
        # Positive test:rule will delete when peer group deleting
        # Creating a Security Group to add rules to it
        s1_name = data_utils.rand_name('securitygroup1-')
        s1_description = data_utils.rand_name('description1-')
        resp, sg1 = \
            self.client.create_security_group(s1_name, s1_description)
        self.addCleanup(self.client.delete_security_group, sg1['id'])
        self.assertEqual(200, resp.status)
        # Creating other Security Group to access to group1
        s2_name = data_utils.rand_name('securitygroup2-')
        s2_description = data_utils.rand_name('description2-')
        resp, sg2 = \
            self.client.create_security_group(s2_name, s2_description)
        self.assertEqual(200, resp.status)
        sg2_id = sg2['id']
        # Adding rules to the Group1
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        resp, rule = \
            self.client.create_security_group_rule(sg1['id'],
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
            self.client.list_security_group_rules(sg1['id'])
        # The group1 has no rules because group2 has deleted
        self.assertEqual(0, len(rules))


class SecurityGroupRulesTestXML(SecurityGroupRulesTestJSON):
    _interface = 'xml'
