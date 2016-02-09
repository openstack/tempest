# Copyright 2013 OpenStack, LLC
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

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import test


class ProjectsTestJSON(base.BaseIdentityV3AdminTest):

    @test.idempotent_id('0ecf465c-0dc4-4532-ab53-91ffeb74d12d')
    def test_project_create_with_description(self):
        # Create project with a description
        project_name = data_utils.rand_name('project')
        project_desc = data_utils.rand_name('desc')
        project = self.projects_client.create_project(
            project_name, description=project_desc)['project']
        self.data.projects.append(project)
        project_id = project['id']
        desc1 = project['description']
        self.assertEqual(desc1, project_desc, 'Description should have '
                         'been sent in response for create')
        body = self.projects_client.show_project(project_id)['project']
        desc2 = body['description']
        self.assertEqual(desc2, project_desc, 'Description does not appear'
                         'to be set')

    @test.idempotent_id('5f50fe07-8166-430b-a882-3b2ee0abe26f')
    def test_project_create_with_domain(self):
        # Create project with a domain
        self.data.setup_test_domain()
        project_name = data_utils.rand_name('project')
        project = self.projects_client.create_project(
            project_name, domain_id=self.data.domain['id'])['project']
        self.data.projects.append(project)
        project_id = project['id']
        self.assertEqual(project_name, project['name'])
        self.assertEqual(self.data.domain['id'], project['domain_id'])
        body = self.projects_client.show_project(project_id)['project']
        self.assertEqual(project_name, body['name'])
        self.assertEqual(self.data.domain['id'], body['domain_id'])

    @test.idempotent_id('1f66dc76-50cc-4741-a200-af984509e480')
    def test_project_create_enabled(self):
        # Create a project that is enabled
        project_name = data_utils.rand_name('project')
        project = self.projects_client.create_project(
            project_name, enabled=True)['project']
        self.data.projects.append(project)
        project_id = project['id']
        en1 = project['enabled']
        self.assertTrue(en1, 'Enable should be True in response')
        body = self.projects_client.show_project(project_id)['project']
        en2 = body['enabled']
        self.assertTrue(en2, 'Enable should be True in lookup')

    @test.idempotent_id('78f96a9c-e0e0-4ee6-a3ba-fbf6dfd03207')
    def test_project_create_not_enabled(self):
        # Create a project that is not enabled
        project_name = data_utils.rand_name('project')
        project = self.projects_client.create_project(
            project_name, enabled=False)['project']
        self.data.projects.append(project)
        en1 = project['enabled']
        self.assertEqual('false', str(en1).lower(),
                         'Enable should be False in response')
        body = self.projects_client.show_project(project['id'])['project']
        en2 = body['enabled']
        self.assertEqual('false', str(en2).lower(),
                         'Enable should be False in lookup')

    @test.idempotent_id('f608f368-048c-496b-ad63-d286c26dab6b')
    def test_project_update_name(self):
        # Update name attribute of a project
        p_name1 = data_utils.rand_name('project')
        project = self.projects_client.create_project(p_name1)['project']
        self.data.projects.append(project)

        resp1_name = project['name']

        p_name2 = data_utils.rand_name('project2')
        body = self.projects_client.update_project(project['id'],
                                                   name=p_name2)['project']
        resp2_name = body['name']
        self.assertNotEqual(resp1_name, resp2_name)

        body = self.projects_client.show_project(project['id'])['project']
        resp3_name = body['name']

        self.assertNotEqual(resp1_name, resp3_name)
        self.assertEqual(p_name1, resp1_name)
        self.assertEqual(resp2_name, resp3_name)

    @test.idempotent_id('f138b715-255e-4a7d-871d-351e1ef2e153')
    def test_project_update_desc(self):
        # Update description attribute of a project
        p_name = data_utils.rand_name('project')
        p_desc = data_utils.rand_name('desc')
        project = self.projects_client.create_project(
            p_name, description=p_desc)['project']
        self.data.projects.append(project)
        resp1_desc = project['description']

        p_desc2 = data_utils.rand_name('desc2')
        body = self.projects_client.update_project(
            project['id'], description=p_desc2)['project']
        resp2_desc = body['description']
        self.assertNotEqual(resp1_desc, resp2_desc)

        body = self.projects_client.show_project(project['id'])['project']
        resp3_desc = body['description']

        self.assertNotEqual(resp1_desc, resp3_desc)
        self.assertEqual(p_desc, resp1_desc)
        self.assertEqual(resp2_desc, resp3_desc)

    @test.idempotent_id('b6b25683-c97f-474d-a595-55d410b68100')
    def test_project_update_enable(self):
        # Update the enabled attribute of a project
        p_name = data_utils.rand_name('project')
        p_en = False
        project = self.projects_client.create_project(p_name,
                                                      enabled=p_en)['project']
        self.data.projects.append(project)

        resp1_en = project['enabled']

        p_en2 = True
        body = self.projects_client.update_project(project['id'],
                                                   enabled=p_en2)['project']
        resp2_en = body['enabled']
        self.assertNotEqual(resp1_en, resp2_en)

        body = self.projects_client.show_project(project['id'])['project']
        resp3_en = body['enabled']

        self.assertNotEqual(resp1_en, resp3_en)
        self.assertEqual('false', str(resp1_en).lower())
        self.assertEqual(resp2_en, resp3_en)

    @test.idempotent_id('59398d4a-5dc5-4f86-9a4c-c26cc804d6c6')
    def test_associate_user_to_project(self):
        # Associate a user to a project
        # Create a Project
        p_name = data_utils.rand_name('project')
        project = self.projects_client.create_project(p_name)['project']
        self.data.projects.append(project)

        # Create a User
        u_name = data_utils.rand_name('user')
        u_desc = u_name + 'description'
        u_email = u_name + '@testmail.tm'
        u_password = data_utils.rand_password()
        user = self.users_client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email, project_id=project['id'])['user']
        # Delete the User at the end of this method
        self.addCleanup(self.users_client.delete_user, user['id'])

        # Get User To validate the user details
        new_user_get = self.users_client.show_user(user['id'])['user']
        # Assert response body of GET
        self.assertEqual(u_name, new_user_get['name'])
        self.assertEqual(u_desc, new_user_get['description'])
        self.assertEqual(project['id'],
                         new_user_get['project_id'])
        self.assertEqual(u_email, new_user_get['email'])
