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
from tempest_lib import decorators
from tempest_lib import exceptions as lib_exc
import testtools

from tempest.api.compute.security_groups import base
from tempest import config
from tempest import test

CONF = config.CONF


class SecurityGroupsNegativeTestJSON(base.BaseSecurityGroupsTest):

    @classmethod
    def setup_clients(cls):
        super(SecurityGroupsNegativeTestJSON, cls).setup_clients()
        cls.client = cls.security_groups_client

    @classmethod
    def resource_setup(cls):
        super(SecurityGroupsNegativeTestJSON, cls).resource_setup()
        cls.neutron_available = CONF.service_available.neutron

    def _generate_a_non_existent_security_group_id(self):
        security_group_id = []
        body = self.client.list_security_groups()
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
    @test.idempotent_id('673eaec1-9b3e-48ed-bdf1-2786c1b9661c')
    @test.services('network')
    def test_security_group_get_nonexistent_group(self):
        # Negative test:Should not be able to GET the details
        # of non-existent Security Group
        non_exist_id = self._generate_a_non_existent_security_group_id()
        self.assertRaises(lib_exc.NotFound, self.client.get_security_group,
                          non_exist_id)

    @decorators.skip_because(bug="1161411",
                             condition=CONF.service_available.neutron)
    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('1759c3cb-b0fc-44b7-86ce-c99236be911d')
    @test.services('network')
    def test_security_group_create_with_invalid_group_name(self):
        # Negative test: Security Group should not be created with group name
        # as an empty string/with white spaces/chars more than 255
        s_description = data_utils.rand_name('description')
        # Create Security Group with empty string as group name
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group, "", s_description)
        # Create Security Group with white space in group name
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group, " ",
                          s_description)
        # Create Security Group with group name longer than 255 chars
        s_name = 'securitygroup-'.ljust(260, '0')
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group, s_name,
                          s_description)

    @decorators.skip_because(bug="1161411",
                             condition=CONF.service_available.neutron)
    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('777b6f14-aca9-4758-9e84-38783cfa58bc')
    @test.services('network')
    def test_security_group_create_with_invalid_group_description(self):
        # Negative test:Security Group should not be created with description
        # as an empty string/with white spaces/chars more than 255
        s_name = data_utils.rand_name('securitygroup')
        # Create Security Group with empty string as description
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group, s_name, "")
        # Create Security Group with white space in description
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group, s_name, " ")
        # Create Security Group with group description longer than 255 chars
        s_description = 'description-'.ljust(260, '0')
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group, s_name,
                          s_description)

    @test.idempotent_id('9fdb4abc-6b66-4b27-b89c-eb215a956168')
    @testtools.skipIf(CONF.service_available.neutron,
                      "Neutron allows duplicate names for security groups")
    @test.attr(type=['negative', 'smoke'])
    @test.services('network')
    def test_security_group_create_with_duplicate_name(self):
        # Negative test:Security Group with duplicate name should not
        # be created
        s_name = data_utils.rand_name('securitygroup')
        s_description = data_utils.rand_name('description')
        self.create_security_group(s_name, s_description)
        # Now try the Security Group with the same 'Name'
        self.assertRaises(lib_exc.BadRequest,
                          self.client.create_security_group, s_name,
                          s_description)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('36a1629f-c6da-4a26-b8b8-55e7e5d5cd58')
    @test.services('network')
    def test_delete_the_default_security_group(self):
        # Negative test:Deletion of the "default" Security Group should Fail
        default_security_group_id = None
        body = self.client.list_security_groups()
        for i in range(len(body)):
            if body[i]['name'] == 'default':
                default_security_group_id = body[i]['id']
                break
        # Deleting the "default" Security Group
        self.assertRaises(lib_exc.BadRequest,
                          self.client.delete_security_group,
                          default_security_group_id)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('6727c00b-214c-4f9e-9a52-017ac3e98411')
    @test.services('network')
    def test_delete_nonexistent_security_group(self):
        # Negative test:Deletion of a non-existent Security Group should fail
        non_exist_id = self._generate_a_non_existent_security_group_id()
        self.assertRaises(lib_exc.NotFound,
                          self.client.delete_security_group, non_exist_id)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('1438f330-8fa4-4aeb-8a94-37c250106d7f')
    @test.services('network')
    def test_delete_security_group_without_passing_id(self):
        # Negative test:Deletion of a Security Group with out passing ID
        # should Fail
        self.assertRaises(lib_exc.NotFound,
                          self.client.delete_security_group, '')

    @test.idempotent_id('00579617-fe04-4e1c-9d08-ca7467d2e34b')
    @testtools.skipIf(CONF.service_available.neutron,
                      "Neutron not check the security_group_id")
    @test.attr(type=['negative', 'smoke'])
    @test.services('network')
    def test_update_security_group_with_invalid_sg_id(self):
        # Update security_group with invalid sg_id should fail
        s_name = data_utils.rand_name('sg')
        s_description = data_utils.rand_name('description')
        # Create a non int sg_id
        sg_id_invalid = data_utils.rand_name('sg')
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_security_group, sg_id_invalid,
                          name=s_name, description=s_description)

    @test.idempotent_id('cda8d8b4-59f8-4087-821d-20cf5a03b3b1')
    @testtools.skipIf(CONF.service_available.neutron,
                      "Neutron not check the security_group_name")
    @test.attr(type=['negative', 'smoke'])
    @test.services('network')
    def test_update_security_group_with_invalid_sg_name(self):
        # Update security_group with invalid sg_name should fail
        securitygroup = self.create_security_group()
        self.assertIn('id', securitygroup)
        securitygroup_id = securitygroup['id']
        # Update Security Group with group name longer than 255 chars
        s_new_name = 'securitygroup-'.ljust(260, '0')
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_security_group,
                          securitygroup_id, name=s_new_name)

    @test.idempotent_id('97d12b1c-a610-4194-93f1-ba859e718b45')
    @testtools.skipIf(CONF.service_available.neutron,
                      "Neutron not check the security_group_description")
    @test.attr(type=['negative', 'smoke'])
    @test.services('network')
    def test_update_security_group_with_invalid_sg_des(self):
        # Update security_group with invalid sg_des should fail
        securitygroup = self.create_security_group()
        self.assertIn('id', securitygroup)
        securitygroup_id = securitygroup['id']
        # Update Security Group with group description longer than 255 chars
        s_new_des = 'des-'.ljust(260, '0')
        self.assertRaises(lib_exc.BadRequest,
                          self.client.update_security_group,
                          securitygroup_id, description=s_new_des)

    @test.attr(type=['negative', 'smoke'])
    @test.idempotent_id('27edee9c-873d-4da6-a68a-3c256efebe8f')
    @test.services('network')
    def test_update_non_existent_security_group(self):
        # Update a non-existent Security Group should Fail
        non_exist_id = self._generate_a_non_existent_security_group_id()
        s_name = data_utils.rand_name('sg')
        s_description = data_utils.rand_name('description')
        self.assertRaises(lib_exc.NotFound,
                          self.client.update_security_group,
                          non_exist_id, name=s_name,
                          description=s_description)
