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

import testtools

from tempest.api.compute.security_groups import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class SecurityGroupsNegativeTestJSON(base.BaseSecurityGroupsTest):

    @classmethod
    def setUpClass(cls):
        super(SecurityGroupsNegativeTestJSON, cls).setUpClass()
        cls.client = cls.security_groups_client
        cls.neutron_available = CONF.service_available.neutron

    def _generate_a_non_existent_security_group_id(self):
        security_group_id = []
        resp, body = self.client.list_security_groups()
        for i in range(len(body)):
            security_group_id.append(body[i]['id'])
        # Generate a non-existent security group id
        while True:
            non_exist_id = data_utils.rand_int_id(start=999)
            if self.neutron_available:
                non_exist_id = data_utils.rand_uuid()
            if non_exist_id not in security_group_id:
                break
        return non_exist_id

    @test.attr(type=['negative', 'smoke'])
    def test_security_group_get_nonexistent_group(self):
        # Negative test:Should not be able to GET the details
        # of non-existent Security Group
        non_exist_id = self._generate_a_non_existent_security_group_id()
        self.assertRaises(exceptions.NotFound, self.client.get_security_group,
                          non_exist_id)

    @test.skip_because(bug="1161411",
                       condition=CONF.service_available.neutron)
    @test.attr(type=['negative', 'smoke'])
    def test_security_group_create_with_invalid_group_name(self):
        # Negative test: Security Group should not be created with group name
        # as an empty string/with white spaces/chars more than 255
        s_description = data_utils.rand_name('description-')
        # Create Security Group with empty string as group name
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group, "", s_description)
        # Create Security Group with white space in group name
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group, " ",
                          s_description)
        # Create Security Group with group name longer than 255 chars
        s_name = 'securitygroup-'.ljust(260, '0')
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group, s_name,
                          s_description)

    @test.skip_because(bug="1161411",
                       condition=CONF.service_available.neutron)
    @test.attr(type=['negative', 'smoke'])
    def test_security_group_create_with_invalid_group_description(self):
        # Negative test:Security Group should not be created with description
        # as an empty string/with white spaces/chars more than 255
        s_name = data_utils.rand_name('securitygroup-')
        # Create Security Group with empty string as description
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group, s_name, "")
        # Create Security Group with white space in description
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group, s_name, " ")
        # Create Security Group with group description longer than 255 chars
        s_description = 'description-'.ljust(260, '0')
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group, s_name,
                          s_description)

    @testtools.skipIf(CONF.service_available.neutron,
                      "Neutron allows duplicate names for security groups")
    @test.attr(type=['negative', 'smoke'])
    def test_security_group_create_with_duplicate_name(self):
        # Negative test:Security Group with duplicate name should not
        # be created
        s_name = data_utils.rand_name('securitygroup-')
        s_description = data_utils.rand_name('description-')
        resp, security_group =\
            self.create_security_group(s_name, s_description)
        self.assertEqual(200, resp.status)
        # Now try the Security Group with the same 'Name'
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group, s_name,
                          s_description)

    @test.attr(type=['negative', 'smoke'])
    def test_delete_the_default_security_group(self):
        # Negative test:Deletion of the "default" Security Group should Fail
        default_security_group_id = None
        resp, body = self.client.list_security_groups()
        for i in range(len(body)):
            if body[i]['name'] == 'default':
                default_security_group_id = body[i]['id']
                break
        # Deleting the "default" Security Group
        self.assertRaises(exceptions.BadRequest,
                          self.client.delete_security_group,
                          default_security_group_id)

    @test.attr(type=['negative', 'smoke'])
    def test_delete_nonexistent_security_group(self):
        # Negative test:Deletion of a non-existent Security Group should fail
        non_exist_id = self._generate_a_non_existent_security_group_id()
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_security_group, non_exist_id)

    @test.attr(type=['negative', 'smoke'])
    def test_delete_security_group_without_passing_id(self):
        # Negative test:Deletion of a Security Group with out passing ID
        # should Fail
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_security_group, '')

    @testtools.skipIf(CONF.service_available.neutron,
                      "Neutron not check the security_group_id")
    @test.attr(type=['negative', 'smoke'])
    def test_update_security_group_with_invalid_sg_id(self):
        # Update security_group with invalid sg_id should fail
        s_name = data_utils.rand_name('sg-')
        s_description = data_utils.rand_name('description-')
        # Create a non int sg_id
        sg_id_invalid = data_utils.rand_name('sg-')
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_security_group, sg_id_invalid,
                          name=s_name, description=s_description)

    @testtools.skipIf(CONF.service_available.neutron,
                      "Neutron not check the security_group_name")
    @test.attr(type=['negative', 'smoke'])
    def test_update_security_group_with_invalid_sg_name(self):
        # Update security_group with invalid sg_name should fail
        resp, securitygroup = self.create_security_group()
        self.assertEqual(200, resp.status)
        self.assertIn('id', securitygroup)
        securitygroup_id = securitygroup['id']
        # Update Security Group with group name longer than 255 chars
        s_new_name = 'securitygroup-'.ljust(260, '0')
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_security_group,
                          securitygroup_id, name=s_new_name)

    @testtools.skipIf(CONF.service_available.neutron,
                      "Neutron not check the security_group_description")
    @test.attr(type=['negative', 'smoke'])
    def test_update_security_group_with_invalid_sg_des(self):
        # Update security_group with invalid sg_des should fail
        resp, securitygroup = self.create_security_group()
        self.assertEqual(200, resp.status)
        self.assertIn('id', securitygroup)
        securitygroup_id = securitygroup['id']
        # Update Security Group with group description longer than 255 chars
        s_new_des = 'des-'.ljust(260, '0')
        self.assertRaises(exceptions.BadRequest,
                          self.client.update_security_group,
                          securitygroup_id, description=s_new_des)

    @test.attr(type=['negative', 'smoke'])
    def test_update_non_existent_security_group(self):
        # Update a non-existent Security Group should Fail
        non_exist_id = self._generate_a_non_existent_security_group_id()
        s_name = data_utils.rand_name('sg-')
        s_description = data_utils.rand_name('description-')
        self.assertRaises(exceptions.NotFound,
                          self.client.update_security_group,
                          non_exist_id, name=s_name,
                          description=s_description)


class SecurityGroupsNegativeTestXML(SecurityGroupsNegativeTestJSON):
    _interface = 'xml'
