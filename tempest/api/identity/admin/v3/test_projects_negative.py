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

from tempest.api.identity import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class ProjectsNegativeTestJSON(base.BaseIdentityV3AdminTest):
    """Negative tests of projects"""

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8d68c012-89e0-4394-8d6b-ccd7196def97')
    def test_project_delete_by_unauthorized_user(self):
        """Non-admin user should not be able to delete a project"""
        project = self.setup_test_project()
        self.assertRaises(
            lib_exc.Forbidden, self.non_admin_projects_client.delete_project,
            project['id'])


class ProjectsNegativeStaticTestJSON(base.BaseIdentityV3AdminTest):
    """Negative tests of projects

    These tests can be executed in clouds using the pre-provisioned users
    """

    # NOTE: force_tenant_isolation is true in the base class by default but
    # overridden to false here to allow test execution for clouds using the
    # pre-provisioned credentials provider.
    force_tenant_isolation = False

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('24c49279-45dd-4155-887a-cb738c2385aa')
    def test_list_projects_by_unauthorized_user(self):
        """Non-admin user should not be able to list projects"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_projects_client.list_projects)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('874c3e84-d174-4348-a16b-8c01f599561b')
    def test_project_create_duplicate(self):
        """Project names should be unique"""
        project_name = data_utils.rand_name(
            name='project-dup', prefix=CONF.resource_name_prefix)
        self.setup_test_project(name=project_name)

        self.assertRaises(lib_exc.Conflict,
                          self.projects_client.create_project, project_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8fba9de2-3e1f-4e77-812a-60cb68f8df13')
    def test_create_project_by_unauthorized_user(self):
        """Non-admin user should not be authorized to create a project"""
        project_name = data_utils.rand_name(
            name='project', prefix=CONF.resource_name_prefix)
        self.assertRaises(
            lib_exc.Forbidden, self.non_admin_projects_client.create_project,
            project_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7828db17-95e5-475b-9432-9a51b4aa79a9')
    def test_create_project_with_empty_name(self):
        """Project name should not be empty"""
        self.assertRaises(lib_exc.BadRequest,
                          self.projects_client.create_project, name='')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('502b6ceb-b0c8-4422-bf53-f08fdb21e2f0')
    def test_create_projects_name_length_over_64(self):
        """Project name length should not be greater than 64 characters"""
        project_name = 'a' * 65
        self.assertRaises(lib_exc.BadRequest,
                          self.projects_client.create_project, project_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7965b581-60c1-43b7-8169-95d4ab7fc6fb')
    def test_delete_non_existent_project(self):
        """Attempt to delete a non existent project should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.projects_client.delete_project,
                          data_utils.rand_uuid_hex())
