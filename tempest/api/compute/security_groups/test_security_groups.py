# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import testtools
import uuid	
from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest.test import attr
from tempest.test import skip_because


class SecurityGroupsTestJSON(base.BaseComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(SecurityGroupsTestJSON, cls).setUpClass()
        cls.client = cls.security_groups_client
        cls.neutron_available = cls.config.service_available.neutron	

    def _delete_security_group(self, securitygroup_id):
        resp, _ = self.client.delete_security_group(securitygroup_id)
        self.assertEqual(202, resp.status)

    @attr(type='gate')
    def test_security_groups_create_list_delete(self):
        # Positive test:Should return the list of Security Groups
        # Create 3 Security Groups
        security_group_list = list()
        for i in range(3):
            s_name = data_utils.rand_name('securitygroup-')
            s_description = data_utils.rand_name('description-')
            resp, securitygroup = \
                self.client.create_security_group(s_name, s_description)
            self.assertEqual(200, resp.status)
            self.addCleanup(self._delete_security_group,
                            securitygroup['id'])
            security_group_list.append(securitygroup)
        # Fetch all Security Groups and verify the list
        # has all created Security Groups
        resp, fetched_list = self.client.list_security_groups()
        self.assertEqual(200, resp.status)
        # Now check if all the created Security Groups are in fetched list
        missing_sgs = \
            [sg for sg in security_group_list if sg not in fetched_list]
        self.assertFalse(missing_sgs,
                         "Failed to find Security Group %s in fetched "
                         "list" % ', '.join(m_group['name']
                                            for m_group in missing_sgs))

    # TODO(afazekas): scheduled for delete,
    # test_security_group_create_get_delete covers it
    @attr(type='gate')
    def test_security_group_create_delete(self):
        # Security Group should be created, verified and deleted
        s_name = data_utils.rand_name('securitygroup-')
        s_description = data_utils.rand_name('description-')
        resp, securitygroup = \
            self.client.create_security_group(s_name, s_description)
        self.assertIn('id', securitygroup)
        securitygroup_id = securitygroup['id']
        self.addCleanup(self._delete_security_group,
                        securitygroup_id)
        self.assertEqual(200, resp.status)
        self.assertFalse(securitygroup_id is None)
        self.assertIn('name', securitygroup)
        securitygroup_name = securitygroup['name']
        self.assertEqual(securitygroup_name, s_name,
                         "The created Security Group name is "
                         "not equal to the requested name")

    @attr(type='gate')
    def test_security_group_create_get_delete(self):
        # Security Group should be created, fetched and deleted
        s_name = data_utils.rand_name('securitygroup-')
        s_description = data_utils.rand_name('description-')
        resp, securitygroup = \
            self.client.create_security_group(s_name, s_description)
        self.addCleanup(self._delete_security_group,
                        securitygroup['id'])

        self.assertEqual(200, resp.status)
        self.assertIn('name', securitygroup)
        securitygroup_name = securitygroup['name']
        self.assertEqual(securitygroup_name, s_name,
                         "The created Security Group name is "
                         "not equal to the requested name")
        # Now fetch the created Security Group by its 'id'
        resp, fetched_group = \
            self.client.get_security_group(securitygroup['id'])
        self.assertEqual(200, resp.status)
        self.assertEqual(securitygroup, fetched_group,
                         "The fetched Security Group is different "
                         "from the created Group")
    @attr(type=['negative', 'smoke'])	
    def test_security_group_get_nonexistant_group(self):
        # Negative test:Should not be able to GET the details
        # of non-existent Security Group
        security_group_id = []
        resp, body = self.client.list_security_groups()
        for i in range(len(body)):
            security_group_id.append(body[i]['id'])
        # Creating a non-existent Security Group id
        while True:
            non_exist_id = data_utils.rand_int_id(start=999)
            if self.neutron_available:
                print "neutron is available"
                non_exist_id = str(uuid.uuid4())
            if non_exist_id not in security_group_id:
                break
        self.assertRaises(exceptions.NotFound, self.client.get_security_group,
                          non_exist_id)

    @skip_because(bug="1161411",
                  condition=config.TempestConfig().service_available.neutron)
    @attr(type=['negative', 'gate'])
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

    @skip_because(bug="1161411",
                  condition=config.TempestConfig().service_available.neutron)
    @attr(type=['negative', 'gate'])
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

    @testtools.skipIf(config.TempestConfig().service_available.neutron,
                      "Neutron allows duplicate names for security groups")
    @attr(type=['negative', 'gate'])
    def test_security_group_create_with_duplicate_name(self):
        # Negative test:Security Group with duplicate name should not
        # be created
        s_name = data_utils.rand_name('securitygroup-')
        s_description = data_utils.rand_name('description-')
        resp, security_group =\
            self.client.create_security_group(s_name, s_description)
        self.assertEqual(200, resp.status)

        self.addCleanup(self.client.delete_security_group,
                        security_group['id'])
        # Now try the Security Group with the same 'Name'
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_security_group, s_name,
                          s_description)

    @attr(type=['negative', 'gate'])
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
    @attr(type=['negative', 'smoke'])	
    def test_delete_nonexistant_security_group(self):
        # Negative test:Deletion of a non-existent Security Group should Fail
        security_group_id = []
        resp, body = self.client.list_security_groups()
        for i in range(len(body)):
            security_group_id.append(body[i]['id'])
        # Creating non-existent Security Group
        while True:
            non_exist_id = data_utils.rand_int_id(start=999)
            if self.neutron_available:
                non_exist_id = str(uuid.uuid4())
            if non_exist_id not in security_group_id:
                break
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_security_group, non_exist_id)

    @attr(type=['negative', 'gate'])
    def test_delete_security_group_without_passing_id(self):
        # Negative test:Deletion of a Security Group with out passing ID
        # should Fail
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_security_group, '')

    @attr(type='gate')
    def test_server_security_groups(self):
        # Checks that security groups may be added and linked to a server
        # and not deleted if the server is active.
        # Create a couple security groups that we will use
        # for the server resource this test creates
        sg_name = data_utils.rand_name('sg')
        sg_desc = data_utils.rand_name('sg-desc')
        resp, sg = self.client.create_security_group(sg_name, sg_desc)
        sg_id = sg['id']

        sg2_name = data_utils.rand_name('sg')
        sg2_desc = data_utils.rand_name('sg-desc')
        resp, sg2 = self.client.create_security_group(sg2_name, sg2_desc)
        sg2_id = sg2['id']

        # Create server and add the security group created
        # above to the server we just created
        server_name = data_utils.rand_name('server')
        resp, server = self.servers_client.create_server(server_name,
                                                         self.image_ref,
                                                         self.flavor_ref)
        server_id = server['id']
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')
        resp, body = self.servers_client.add_security_group(server_id,
                                                            sg_name)

        # Check that we are not able to delete the security
        # group since it is in use by an active server
        self.assertRaises(exceptions.BadRequest,
                          self.client.delete_security_group,
                          sg_id)

        # Reboot and add the other security group
        resp, body = self.servers_client.reboot(server_id, 'HARD')
        self.servers_client.wait_for_server_status(server_id, 'ACTIVE')
        resp, body = self.servers_client.add_security_group(server_id,
                                                            sg2_name)

        # Check that we are not able to delete the other security
        # group since it is in use by an active server
        self.assertRaises(exceptions.BadRequest,
                          self.client.delete_security_group,
                          sg2_id)

        # Shutdown the server and then verify we can destroy the
        # security groups, since no active server instance is using them
        self.servers_client.delete_server(server_id)
        self.servers_client.wait_for_server_termination(server_id)

        self.client.delete_security_group(sg_id)
        self.assertEqual(202, resp.status)

        self.client.delete_security_group(sg2_id)
        self.assertEqual(202, resp.status)


class SecurityGroupsTestXML(SecurityGroupsTestJSON):
    _interface = 'xml'
