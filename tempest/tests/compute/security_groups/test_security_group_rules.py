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

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr
from tempest.tests.compute import base


class SecurityGroupRulesTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(SecurityGroupRulesTestJSON, cls).setUpClass()
        cls.client = cls.security_groups_client

    @attr(type='positive')
    def test_security_group_rules_create(self):
        # Positive test: Creation of Security Group rule
        # should be successfull
        try:
            #Creating a Security Group to add rules to it
            s_name = rand_name('securitygroup-')
            s_description = rand_name('description-')
            resp, securitygroup =\
            self.client.create_security_group(s_name, s_description)
            securitygroup_id = securitygroup['id']
            #Adding rules to the created Security Group
            parent_group_id = securitygroup['id']
            ip_protocol = 'tcp'
            from_port = 22
            to_port = 22
            resp, rule =\
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol, from_port,
                                                   to_port)
            self.assertEqual(200, resp.status)
        finally:
            #Deleting the Security Group rule, created in this method
            group_rule_id = rule['id']
            self.client.delete_security_group_rule(group_rule_id)
            #Deleting the Security Group created in this method
            resp, _ = self.client.delete_security_group(securitygroup_id)

    @attr(type='positive')
    def test_security_group_rules_create_with_optional_arguments(self):
        # Positive test: Creation of Security Group rule
        # with optional arguments
        # should be successfull

        rule_id = None
        secgroup1 = None
        secgroup2 = None
        try:
            #Creating a Security Group to add rules to it
            s_name = rand_name('securitygroup-')
            s_description = rand_name('description-')
            resp, securitygroup =\
            self.client.create_security_group(s_name, s_description)
            secgroup1 = securitygroup['id']
            #Creating a Security Group so as to assign group_id to the rule
            s_name2 = rand_name('securitygroup-')
            s_description2 = rand_name('description-')
            resp, securitygroup =\
            self.client.create_security_group(s_name2, s_description2)
            secgroup2 = securitygroup['id']
            #Adding rules to the created Security Group with optional arguments
            parent_group_id = secgroup1
            ip_protocol = 'tcp'
            from_port = 22
            to_port = 22
            cidr = '10.2.3.124/24'
            group_id = secgroup2
            resp, rule =\
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol,
                                                   from_port, to_port,
                                                   cidr=cidr,
                                                   group_id=group_id)
            rule_id = rule['id']
            self.assertEqual(200, resp.status)
        finally:
            #Deleting the Security Group rule, created in this method
            if rule_id:
                self.client.delete_security_group_rule(rule_id)
            #Deleting the Security Groups created in this method
            if secgroup1:
                self.client.delete_security_group(secgroup1)
            if secgroup2:
                self.client.delete_security_group(secgroup2)

    @attr(type='positive')
    def test_security_group_rules_create_delete(self):
        # Positive test: Deletion of Security Group rule
        # should be successfull
        try:
            #Creating a Security Group to add rule to it
            s_name = rand_name('securitygroup-')
            s_description = rand_name('description-')
            resp, securitygroup =\
            self.client.create_security_group(s_name, s_description)
            securitygroup_id = securitygroup['id']
            #Adding rules to the created Security Group
            parent_group_id = securitygroup['id']
            ip_protocol = 'tcp'
            from_port = 22
            to_port = 22
            resp, rule =\
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol,
                                                   from_port, to_port)
        finally:
            #Deleting the Security Group rule, created in this method
            group_rule_id = rule['id']
            self.client.delete_security_group_rule(group_rule_id)
            #Deleting the Security Group created in this method
            resp, _ = self.client.delete_security_group(securitygroup_id)

    @attr(type='negative')
    def test_security_group_rules_create_with_invalid_id(self):
        # Negative test: Creation of Security Group rule should FAIL
        # with invalid Parent group id
        #Adding rules to the invalid Security Group id
        parent_group_id = rand_name('999')
        ip_protocol = 'tcp'
        from_port = 22
        to_port = 22
        try:
            resp, rule =\
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol,
                                                   from_port, to_port)
        except exceptions.NotFound:
            pass
        else:
            self.fail('Security Group rule should not be created '
                      'with invalid parent group id')

    @attr(type='negative')
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
        try:
            resp, rule =\
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol,
                                                   from_port, to_port)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Security Group rule should not be created '
                      'with invalid ip_protocol')
        #Deleting the Security Group created in this method
        resp, _ = self.client.delete_security_group(securitygroup['id'])

    @attr(type='negative')
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
        try:
            resp, rule =\
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol,
                                                   from_port, to_port)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Security Group rule should not be created'
                      'with invalid from_port')
        #Deleting the Security Group created in this method
        resp, _ = self.client.delete_security_group(securitygroup['id'])

    @attr(type='negative')
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
        try:
            resp, rule =\
            self.client.create_security_group_rule(parent_group_id,
                                                   ip_protocol,
                                                   from_port, to_port)
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Security Group rule should not be created'
                      'with invalid from_port')
        #Deleting the Security Group created in this method
        resp, _ = self.client.delete_security_group(securitygroup['id'])

    @attr(type='negative')
    def test_security_group_rules_delete_with_invalid_id(self):
        # Negative test: Deletion of Security Group rule should be FAIL
        # with invalid rule id
        try:
            self.client.delete_security_group_rule(rand_name('999'))
        except exceptions.NotFound:
            pass
        else:
            self.fail('Security Group Rule should not be deleted '
                      'with nonexistant rule id')


class SecurityGroupRulesTestXML(SecurityGroupRulesTestJSON):
    _interface = 'xml'
