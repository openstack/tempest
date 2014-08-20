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
    _interface = 'json'

    @test.attr(type='gate')
    def test_project_create_with_description(self):
        # Create project with a description
        project_name = data_utils.rand_name('project-')
        project_desc = data_utils.rand_name('desc-')
        _, project = self.client.create_project(
            project_name, description=project_desc)
        self.data.projects.append(project)
        project_id = project['id']
        desc1 = project['description']
        self.assertEqual(desc1, project_desc, 'Description should have '
                         'been sent in response for create')
        _, body = self.client.get_project(project_id)
        desc2 = body['description']
        self.assertEqual(desc2, project_desc, 'Description does not appear'
                         'to be set')

    @test.attr(type='gate')
    def test_project_create_with_domain(self):
        # Create project with a domain
        self.data.setup_test_domain()
        project_name = data_utils.rand_name('project')
        resp, project = self.client.create_project(
            project_name, domain_id=self.data.domain['id'])
        self.data.projects.append(project)
        project_id = project['id']
        self.assertEqual(project_name, project['name'])
        self.assertEqual(self.data.domain['id'], project['domain_id'])
        _, body = self.client.get_project(project_id)
        self.assertEqual(project_name, body['name'])
        self.assertEqual(self.data.domain['id'], body['domain_id'])

    @test.attr(type='gate')
    def test_project_create_enabled(self):
        # Create a project that is enabled
        project_name = data_utils.rand_name('project-')
        _, project = self.client.create_project(
            project_name, enabled=True)
        self.data.projects.append(project)
        project_id = project['id']
        en1 = project['enabled']
        self.assertTrue(en1, 'Enable should be True in response')
        _, body = self.client.get_project(project_id)
        en2 = body['enabled']
        self.assertTrue(en2, 'Enable should be True in lookup')

    @test.attr(type='gate')
    def test_project_create_not_enabled(self):
        # Create a project that is not enabled
        project_name = data_utils.rand_name('project-')
        _, project = self.client.create_project(
            project_name, enabled=False)
        self.data.projects.append(project)
        en1 = project['enabled']
        self.assertEqual('false', str(en1).lower(),
                         'Enable should be False in response')
        _, body = self.client.get_project(project['id'])
        en2 = body['enabled']
        self.assertEqual('false', str(en2).lower(),
                         'Enable should be False in lookup')

    @test.attr(type='gate')
    def test_project_update_name(self):
        # Update name attribute of a project
        p_name1 = data_utils.rand_name('project-')
        _, project = self.client.create_project(p_name1)
        self.data.projects.append(project)

        resp1_name = project['name']

        p_name2 = data_utils.rand_name('project2-')
        _, body = self.client.update_project(project['id'], name=p_name2)
        resp2_name = body['name']
        self.assertNotEqual(resp1_name, resp2_name)

        _, body = self.client.get_project(project['id'])
        resp3_name = body['name']

        self.assertNotEqual(resp1_name, resp3_name)
        self.assertEqual(p_name1, resp1_name)
        self.assertEqual(resp2_name, resp3_name)

    @test.attr(type='gate')
    def test_project_update_desc(self):
        # Update description attribute of a project
        p_name = data_utils.rand_name('project-')
        p_desc = data_utils.rand_name('desc-')
        _, project = self.client.create_project(
            p_name, description=p_desc)
        self.data.projects.append(project)
        resp1_desc = project['description']

        p_desc2 = data_utils.rand_name('desc2-')
        _, body = self.client.update_project(
            project['id'], description=p_desc2)
        resp2_desc = body['description']
        self.assertNotEqual(resp1_desc, resp2_desc)

        _, body = self.client.get_project(project['id'])
        resp3_desc = body['description']

        self.assertNotEqual(resp1_desc, resp3_desc)
        self.assertEqual(p_desc, resp1_desc)
        self.assertEqual(resp2_desc, resp3_desc)

    @test.attr(type='gate')
    def test_project_update_enable(self):
        # Update the enabled attribute of a project
        p_name = data_utils.rand_name('project-')
        p_en = False
        _, project = self.client.create_project(p_name, enabled=p_en)
        self.data.projects.append(project)

        resp1_en = project['enabled']

        p_en2 = True
        _, body = self.client.update_project(
            project['id'], enabled=p_en2)
        resp2_en = body['enabled']
        self.assertNotEqual(resp1_en, resp2_en)

        _, body = self.client.get_project(project['id'])
        resp3_en = body['enabled']

        self.assertNotEqual(resp1_en, resp3_en)
        self.assertEqual('false', str(resp1_en).lower())
        self.assertEqual(resp2_en, resp3_en)

    @test.attr(type='gate')
    def test_associate_user_to_project(self):
        # Associate a user to a project
        # Create a Project
        p_name = data_utils.rand_name('project-')
        _, project = self.client.create_project(p_name)
        self.data.projects.append(project)

        # Create a User
        u_name = data_utils.rand_name('user-')
        u_desc = u_name + 'description'
        u_email = u_name + '@testmail.tm'
        u_password = data_utils.rand_name('pass-')
        _, user = self.client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email, project_id=project['id'])
        # Delete the User at the end of this method
        self.addCleanup(self.client.delete_user, user['id'])

        # Get User To validate the user details
        _, new_user_get = self.client.get_user(user['id'])
        # Assert response body of GET
        self.assertEqual(u_name, new_user_get['name'])
        self.assertEqual(u_desc, new_user_get['description'])
        self.assertEqual(project['id'],
                         new_user_get['project_id'])
        self.assertEqual(u_email, new_user_get['email'])


class ProjectsTestXML(ProjectsTestJSON):
    _interface = 'xml'
