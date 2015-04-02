# Copyright 2013 OpenStack Foundation
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

from tempest.api.identity import base
from tempest import test


class UsersV3TestJSON(base.BaseIdentityV3AdminTest):

    @test.attr(type='gate')
    @test.idempotent_id('b537d090-afb9-4519-b95d-270b0708e87e')
    def test_user_update(self):
        # Test case to check if updating of user attributes is successful.
        # Creating first user
        u_name = data_utils.rand_name('user')
        u_desc = u_name + 'description'
        u_email = u_name + '@testmail.tm'
        u_password = data_utils.rand_name('pass')
        user = self.client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email, enabled=False)
        # Delete the User at the end of this method
        self.addCleanup(self.client.delete_user, user['id'])
        # Creating second project for updation
        project = self.client.create_project(
            data_utils.rand_name('project'),
            description=data_utils.rand_name('project-desc'))
        # Delete the Project at the end of this method
        self.addCleanup(self.client.delete_project, project['id'])
        # Updating user details with new values
        u_name2 = data_utils.rand_name('user2')
        u_email2 = u_name2 + '@testmail.tm'
        u_description2 = u_name2 + ' description'
        update_user = self.client.update_user(
            user['id'], name=u_name2, description=u_description2,
            project_id=project['id'],
            email=u_email2, enabled=False)
        self.assertEqual(u_name2, update_user['name'])
        self.assertEqual(u_description2, update_user['description'])
        self.assertEqual(project['id'],
                         update_user['project_id'])
        self.assertEqual(u_email2, update_user['email'])
        self.assertEqual('false', str(update_user['enabled']).lower())
        # GET by id after updation
        new_user_get = self.client.get_user(user['id'])
        # Assert response body of GET after updation
        self.assertEqual(u_name2, new_user_get['name'])
        self.assertEqual(u_description2, new_user_get['description'])
        self.assertEqual(project['id'],
                         new_user_get['project_id'])
        self.assertEqual(u_email2, new_user_get['email'])
        self.assertEqual('false', str(new_user_get['enabled']).lower())

    @test.attr(type='gate')
    @test.idempotent_id('2d223a0e-e457-4a70-9fb1-febe027a0ff9')
    def test_update_user_password(self):
        # Creating User to check password updation
        u_name = data_utils.rand_name('user')
        original_password = data_utils.rand_name('pass')
        user = self.client.create_user(
            u_name, password=original_password)
        # Delete the User at the end all test methods
        self.addCleanup(self.client.delete_user, user['id'])
        # Update user with new password
        new_password = data_utils.rand_name('pass1')
        self.client.update_user_password(user['id'], new_password,
                                         original_password)
        resp = self.token.auth(user_id=user['id'],
                               password=new_password).response
        subject_token = resp['x-subject-token']
        # Perform GET Token to verify and confirm password is updated
        token_details = self.client.get_token(subject_token)
        self.assertEqual(resp['x-subject-token'], subject_token)
        self.assertEqual(token_details['user']['id'], user['id'])
        self.assertEqual(token_details['user']['name'], u_name)

    @test.attr(type='gate')
    @test.idempotent_id('a831e70c-e35b-430b-92ed-81ebbc5437b8')
    def test_list_user_projects(self):
        # List the projects that a user has access upon
        assigned_project_ids = list()
        fetched_project_ids = list()
        u_project = self.client.create_project(
            data_utils.rand_name('project'),
            description=data_utils.rand_name('project-desc'))
        # Delete the Project at the end of this method
        self.addCleanup(self.client.delete_project, u_project['id'])
        # Create a user.
        u_name = data_utils.rand_name('user')
        u_desc = u_name + 'description'
        u_email = u_name + '@testmail.tm'
        u_password = data_utils.rand_name('pass')
        user_body = self.client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email, enabled=False, project_id=u_project['id'])
        # Delete the User at the end of this method
        self.addCleanup(self.client.delete_user, user_body['id'])
        # Creating Role
        role_body = self.client.create_role(
            data_utils.rand_name('role'))
        # Delete the Role at the end of this method
        self.addCleanup(self.client.delete_role, role_body['id'])

        user = self.client.get_user(user_body['id'])
        role = self.client.get_role(role_body['id'])
        for i in range(2):
            # Creating project so as to assign role
            project_body = self.client.create_project(
                data_utils.rand_name('project'),
                description=data_utils.rand_name('project-desc'))
            project = self.client.get_project(project_body['id'])
            # Delete the Project at the end of this method
            self.addCleanup(self.client.delete_project, project_body['id'])
            # Assigning roles to user on project
            self.client.assign_user_role(project['id'],
                                         user['id'],
                                         role['id'])
            assigned_project_ids.append(project['id'])
        body = self.client.list_user_projects(user['id'])
        for i in body:
            fetched_project_ids.append(i['id'])
        # verifying the project ids in list
        missing_projects =\
            [p for p in assigned_project_ids
             if p not in fetched_project_ids]
        self.assertEqual(0, len(missing_projects),
                         "Failed to find project %s in fetched list" %
                         ', '.join(m_project for m_project
                                   in missing_projects))

    @test.attr(type='gate')
    @test.idempotent_id('c10dcd90-461d-4b16-8e23-4eb836c00644')
    def test_get_user(self):
        # Get a user detail
        self.data.setup_test_v3_user()
        user = self.client.get_user(self.data.v3_user['id'])
        self.assertEqual(self.data.v3_user['id'], user['id'])
