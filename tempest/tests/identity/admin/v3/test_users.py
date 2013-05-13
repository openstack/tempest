# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from tempest.common.utils.data_utils import rand_name
from tempest.test import attr
from tempest.tests.identity import base


class UsersV3TestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    @attr('smoke')
    def test_user_update(self):
        # Test case to check if updating of user attributes is successful.
        #Creating first user
        u_name = rand_name('user-')
        u_desc = u_name + 'description'
        u_email = u_name + '@testmail.tm'
        u_password = rand_name('pass-')
        resp, user = self.v3_client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email, enabled=False)
        # Delete the User at the end of this method
        self.addCleanup(self.v3_client.delete_user, user['id'])
        #Creating second project for updation
        resp, project = self.v3_client.create_project(
            rand_name('project-'), description=rand_name('project-desc-'))
        # Delete the Project at the end of this method
        self.addCleanup(self.v3_client.delete_project, project['id'])
        #Updating user details with new values
        u_name2 = rand_name('user2-')
        u_email2 = u_name2 + '@testmail.tm'
        u_description2 = u_name2 + ' description'
        resp, update_user = self.v3_client.update_user(
            user['id'], name=u_name2, description=u_description2,
            project_id=project['id'],
            email=u_email2, enabled=False)
        #Assert response body of update user.
        self.assertEqual(200, resp.status)
        self.assertEqual(u_name2, update_user['name'])
        self.assertEqual(u_description2, update_user['description'])
        self.assertEqual(project['id'],
                         update_user['project_id'])
        self.assertEqual(u_email2, update_user['email'])
        self.assertEqual('false', str(update_user['enabled']).lower())
        #GET by id after updation
        resp, new_user_get = self.v3_client.get_user(user['id'])
        #Assert response body of GET after updation
        self.assertEqual(u_name2, new_user_get['name'])
        self.assertEqual(u_description2, new_user_get['description'])
        self.assertEqual(project['id'],
                         new_user_get['project_id'])
        self.assertEqual(u_email2, new_user_get['email'])
        self.assertEqual('false', str(new_user_get['enabled']).lower())

    @attr('smoke')
    def test_list_user_projects(self):
        #List the projects that a user has access upon
        assigned_project_ids = list()
        fetched_project_ids = list()
        _, u_project = self.v3_client.create_project(
            rand_name('project-'), description=rand_name('project-desc-'))
        # Delete the Project at the end of this method
        self.addCleanup(self.v3_client.delete_project, u_project['id'])
        #Create a user.
        u_name = rand_name('user-')
        u_desc = u_name + 'description'
        u_email = u_name + '@testmail.tm'
        u_password = rand_name('pass-')
        _, user_body = self.v3_client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email, enabled=False, project_id=u_project['id'])
        # Delete the User at the end of this method
        self.addCleanup(self.v3_client.delete_user, user_body['id'])
        # Creating Role
        _, role_body = self.v3_client.create_role(rand_name('role-'))
        # Delete the Role at the end of this method
        self.addCleanup(self.v3_client.delete_role, role_body['id'])

        _, user = self.v3_client.get_user(user_body['id'])
        _, role = self.v3_client.get_role(role_body['id'])
        for i in range(2):
            # Creating project so as to assign role
            _, project_body = self.v3_client.create_project(
                rand_name('project-'), description=rand_name('project-desc-'))
            _, project = self.v3_client.get_project(project_body['id'])
            # Delete the Project at the end of this method
            self.addCleanup(self.v3_client.delete_project, project_body['id'])
            #Assigning roles to user on project
            self.v3_client.assign_user_role(project['id'],
                                            user['id'],
                                            role['id'])
            assigned_project_ids.append(project['id'])
        resp, body = self.v3_client.list_user_projects(user['id'])
        self.assertEqual(200, resp.status)
        for i in body:
            fetched_project_ids.append(i['id'])
        #verifying the project ids in list
        missing_projects =\
            [p for p in assigned_project_ids
             if p not in fetched_project_ids]
        self.assertEqual(0, len(missing_projects),
                         "Failed to find project %s in fetched list" %
                         ', '.join(m_project for m_project
                         in missing_projects))


class UsersV3TestXML(UsersV3TestJSON):
    _interface = 'xml'
