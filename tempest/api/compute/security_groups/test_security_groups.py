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
from tempest.common import waiters
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class SecurityGroupsTestJSON(base.BaseSecurityGroupsTest):

    @classmethod
    def setup_clients(cls):
        super(SecurityGroupsTestJSON, cls).setup_clients()
        cls.client = cls.security_groups_client

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('eb2b087d-633d-4d0d-a7bd-9e6ba35b32de')
    def test_security_groups_create_list_delete(self):
        # Positive test:Should return the list of Security Groups
        # Create 3 Security Groups
        security_group_list = []
        for _ in range(3):
            body = self.create_security_group()
            security_group_list.append(body)
        # Fetch all Security Groups and verify the list
        # has all created Security Groups
        fetched_list = self.client.list_security_groups()['security_groups']
        # Now check if all the created Security Groups are in fetched list
        missing_sgs = \
            [sg for sg in security_group_list if sg not in fetched_list]
        self.assertFalse(missing_sgs,
                         "Failed to find Security Group %s in fetched "
                         "list" % ', '.join(m_group['name']
                                            for m_group in missing_sgs))
        # Delete all security groups
        for sg in security_group_list:
            self.client.delete_security_group(sg['id'])
            self.client.wait_for_resource_deletion(sg['id'])
        # Now check if all the created Security Groups are deleted
        fetched_list = self.client.list_security_groups()['security_groups']
        deleted_sgs = [sg for sg in security_group_list if sg in fetched_list]
        self.assertFalse(deleted_sgs,
                         "Failed to delete Security Group %s "
                         "list" % ', '.join(m_group['name']
                                            for m_group in deleted_sgs))

    @decorators.idempotent_id('ecc0da4a-2117-48af-91af-993cca39a615')
    def test_security_group_create_get_delete(self):
        # Security Group should be created, fetched and deleted
        # with char space between name along with
        # leading and trailing spaces
        s_name = ' %s ' % data_utils.rand_name('securitygroup ')
        securitygroup = self.create_security_group(name=s_name)
        securitygroup_name = securitygroup['name']
        self.assertEqual(securitygroup_name, s_name,
                         "The created Security Group name is "
                         "not equal to the requested name")
        # Now fetch the created Security Group by its 'id'
        fetched_group = (self.client.show_security_group(securitygroup['id'])
                         ['security_group'])
        self.assertEqual(securitygroup, fetched_group,
                         "The fetched Security Group is different "
                         "from the created Group")
        self.client.delete_security_group(securitygroup['id'])
        self.client.wait_for_resource_deletion(securitygroup['id'])

    @decorators.idempotent_id('fe4abc0d-83f5-4c50-ad11-57a1127297a2')
    def test_server_security_groups(self):
        # Checks that security groups may be added and linked to a server
        # and not deleted if the server is active.
        # Create a couple security groups that we will use
        # for the server resource this test creates
        sg = self.create_security_group()
        sg2 = self.create_security_group()

        # Create server and add the security group created
        # above to the server we just created
        server = self.create_test_server(wait_until='ACTIVE')
        server_id = server['id']
        self.servers_client.add_security_group(server_id, name=sg['name'])

        # Check that we are not able to delete the security
        # group since it is in use by an active server
        self.assertRaises(lib_exc.BadRequest,
                          self.client.delete_security_group,
                          sg['id'])

        # Reboot and add the other security group
        self.servers_client.reboot_server(server_id, type='HARD')
        waiters.wait_for_server_status(self.servers_client, server_id,
                                       'ACTIVE')
        self.servers_client.add_security_group(server_id, name=sg2['name'])

        # Check that we are not able to delete the other security
        # group since it is in use by an active server
        self.assertRaises(lib_exc.BadRequest,
                          self.client.delete_security_group,
                          sg2['id'])

        # Shutdown the server and then verify we can destroy the
        # security groups, since no active server instance is using them
        self.servers_client.delete_server(server_id)
        waiters.wait_for_server_termination(self.servers_client, server_id)

        self.client.delete_security_group(sg['id'])
        self.client.delete_security_group(sg2['id'])

    @decorators.idempotent_id('7d4e1d3c-3209-4d6d-b020-986304ebad1f')
    def test_update_security_groups(self):
        # Update security group name and description
        # Create a security group
        securitygroup = self.create_security_group()
        securitygroup_id = securitygroup['id']
        # Update the name and description
        s_new_name = data_utils.rand_name('sg-hth')
        s_new_des = data_utils.rand_name('description-hth')
        self.client.update_security_group(securitygroup_id,
                                          name=s_new_name,
                                          description=s_new_des)
        # get the security group
        fetched_group = (self.client.show_security_group(securitygroup_id)
                         ['security_group'])
        self.assertEqual(s_new_name, fetched_group['name'])
        self.assertEqual(s_new_des, fetched_group['description'])

    @decorators.idempotent_id('79517d60-535a-438f-af3d-e6feab1cbea7')
    def test_list_security_groups_by_server(self):
        # Create a couple security groups that we will use
        # for the server resource this test creates
        sg = self.create_security_group()
        sg2 = self.create_security_group()
        assigned_security_groups_ids = [sg['id'], sg2['id']]
        # Create server and add the security group created
        # above to the server we just created
        server_id = self.create_test_server(wait_until='ACTIVE')['id']
        # add security groups to server
        self.servers_client.add_security_group(server_id, name=sg['name'])
        self.servers_client.add_security_group(server_id, name=sg2['name'])

        # list security groups for a server
        fetched_groups = (
            self.servers_client.list_security_groups_by_server(
                server_id)['security_groups'])
        fetched_security_groups_ids = [i['id'] for i in fetched_groups]
        # verifying the security groups ids in list
        missing_security_groups =\
            [p for p in assigned_security_groups_ids
             if p not in fetched_security_groups_ids]
        self.assertEmpty(missing_security_groups,
                         "Failed to find security_groups %s in fetched list" %
                         ', '.join(missing_security_groups))
