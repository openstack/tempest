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
from tempest import exceptions
from tempest import test


class ProjectsNegativeTestJSON(base.BaseIdentityV3AdminTest):
    _interface = 'json'

    @test.attr(type=['negative', 'gate'])
    def test_list_projects_by_unauthorized_user(self):
        # Non-admin user should not be able to list projects
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.list_projects)

    @test.attr(type=['negative', 'gate'])
    def test_project_create_duplicate(self):
        # Project names should be unique
        project_name = data_utils.rand_name('project-dup-')
        resp, project = self.client.create_project(project_name)
        self.data.projects.append(project)

        self.assertRaises(
            exceptions.Conflict, self.client.create_project, project_name)

    @test.attr(type=['negative', 'gate'])
    def test_create_project_by_unauthorized_user(self):
        # Non-admin user should not be authorized to create a project
        project_name = data_utils.rand_name('project-')
        self.assertRaises(
            exceptions.Unauthorized, self.non_admin_client.create_project,
            project_name)

    @test.attr(type=['negative', 'gate'])
    def test_create_project_with_empty_name(self):
        # Project name should not be empty
        self.assertRaises(exceptions.BadRequest, self.client.create_project,
                          name='')

    @test.attr(type=['negative', 'gate'])
    def test_create_projects_name_length_over_64(self):
        # Project name length should not be greater than 64 characters
        project_name = 'a' * 65
        self.assertRaises(exceptions.BadRequest, self.client.create_project,
                          project_name)

    @test.attr(type=['negative', 'gate'])
    def test_project_delete_by_unauthorized_user(self):
        # Non-admin user should not be able to delete a project
        project_name = data_utils.rand_name('project-')
        resp, project = self.client.create_project(project_name)
        self.data.projects.append(project)
        self.assertRaises(
            exceptions.Unauthorized, self.non_admin_client.delete_project,
            project['id'])

    @test.attr(type=['negative', 'gate'])
    def test_delete_non_existent_project(self):
        # Attempt to delete a non existent project should fail
        self.assertRaises(exceptions.NotFound, self.client.delete_project,
                          data_utils.rand_uuid_hex())


class ProjectsNegativeTestXML(ProjectsNegativeTestJSON):
    _interface = 'xml'
