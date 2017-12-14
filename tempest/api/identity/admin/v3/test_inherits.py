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
from tempest.common import utils
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class InheritsV3TestJSON(base.BaseIdentityV3AdminTest):

    @classmethod
    def skip_checks(cls):
        super(InheritsV3TestJSON, cls).skip_checks()
        if not utils.is_extension_enabled('OS-INHERIT', 'identity'):
            raise cls.skipException("Inherits aren't enabled")

    @classmethod
    def resource_setup(cls):
        super(InheritsV3TestJSON, cls).resource_setup()
        u_name = data_utils.rand_name('user-')
        u_desc = '%s description' % u_name
        u_email = '%s@testmail.tm' % u_name
        u_password = data_utils.rand_name('pass-')
        cls.domain = cls.create_domain()
        cls.project = cls.projects_client.create_project(
            data_utils.rand_name('project-'),
            description=data_utils.rand_name('project-desc-'),
            domain_id=cls.domain['id'])['project']
        cls.addClassResourceCleanup(cls.projects_client.delete_project,
                                    cls.project['id'])
        cls.group = cls.groups_client.create_group(
            name=data_utils.rand_name('group-'), project_id=cls.project['id'],
            domain_id=cls.domain['id'])['group']
        cls.addClassResourceCleanup(cls.groups_client.delete_group,
                                    cls.group['id'])
        cls.user = cls.users_client.create_user(
            name=u_name, description=u_desc, password=u_password,
            email=u_email, project_id=cls.project['id'],
            domain_id=cls.domain['id'])['user']
        cls.addClassResourceCleanup(cls.users_client.delete_user,
                                    cls.user['id'])

    def _list_assertions(self, body, fetched_role_ids, role_id):
        self.assertEqual(len(body), 1)
        self.assertIn(role_id, fetched_role_ids)

    @decorators.idempotent_id('4e6f0366-97c8-423c-b2be-41eae6ac91c8')
    def test_inherit_assign_list_check_revoke_roles_on_domains_user(self):
        # Create role
        src_role = self.setup_test_role()
        # Assign role on domains user
        self.inherited_roles_client.create_inherited_role_on_domains_user(
            self.domain['id'], self.user['id'], src_role['id'])
        # list role on domains user
        roles = self.inherited_roles_client.\
            list_inherited_project_role_for_user_on_domain(
                self.domain['id'], self.user['id'])['roles']

        fetched_role_ids = [i['id'] for i in roles]
        self._list_assertions(roles, fetched_role_ids,
                              src_role['id'])

        # Check role on domains user
        (self.inherited_roles_client.
         check_user_inherited_project_role_on_domain(
             self.domain['id'], self.user['id'], src_role['id']))
        # Revoke role from domains user.
        self.inherited_roles_client.delete_inherited_role_from_user_on_domain(
            self.domain['id'], self.user['id'], src_role['id'])

    @decorators.idempotent_id('c7a8dda2-be50-4fb4-9a9c-e830771078b1')
    def test_inherit_assign_list_check_revoke_roles_on_domains_group(self):
        # Create role
        src_role = self.setup_test_role()
        # Assign role on domains group
        self.inherited_roles_client.create_inherited_role_on_domains_group(
            self.domain['id'], self.group['id'], src_role['id'])
        # List role on domains group
        roles = self.inherited_roles_client.\
            list_inherited_project_role_for_group_on_domain(
                self.domain['id'], self.group['id'])['roles']

        fetched_role_ids = [i['id'] for i in roles]
        self._list_assertions(roles, fetched_role_ids,
                              src_role['id'])

        # Check role on domains group
        (self.inherited_roles_client.
         check_group_inherited_project_role_on_domain(
             self.domain['id'], self.group['id'], src_role['id']))
        # Revoke role from domains group
        self.inherited_roles_client.delete_inherited_role_from_group_on_domain(
            self.domain['id'], self.group['id'], src_role['id'])

    @decorators.idempotent_id('18b70e45-7687-4b72-8277-b8f1a47d7591')
    def test_inherit_assign_check_revoke_roles_on_projects_user(self):
        # Create role
        src_role = self.setup_test_role()
        # Assign role on projects user
        self.inherited_roles_client.create_inherited_role_on_projects_user(
            self.project['id'], self.user['id'], src_role['id'])
        # Check role on projects user
        (self.inherited_roles_client.
         check_user_has_flag_on_inherited_to_project(
             self.project['id'], self.user['id'], src_role['id']))
        # Revoke role from projects user
        self.inherited_roles_client.delete_inherited_role_from_user_on_project(
            self.project['id'], self.user['id'], src_role['id'])

    @decorators.idempotent_id('26021436-d5a4-4256-943c-ded01e0d4b45')
    def test_inherit_assign_check_revoke_roles_on_projects_group(self):
        # Create role
        src_role = self.setup_test_role()
        # Assign role on projects group
        self.inherited_roles_client.create_inherited_role_on_projects_group(
            self.project['id'], self.group['id'], src_role['id'])
        # Check role on projects group
        (self.inherited_roles_client.
         check_group_has_flag_on_inherited_to_project(
             self.project['id'], self.group['id'], src_role['id']))
        # Revoke role from projects group
        (self.inherited_roles_client.
         delete_inherited_role_from_group_on_project(
             self.project['id'], self.group['id'], src_role['id']))

    @decorators.idempotent_id('3acf666e-5354-42ac-8e17-8b68893bcd36')
    def test_inherit_assign_list_revoke_user_roles_on_domain(self):
        # Create role
        src_role = self.setup_test_role()

        # Create a project hierarchy
        leaf_project = self.setup_test_project(domain_id=self.domain['id'],
                                               parent_id=self.project['id'])

        # Assign role on domain
        self.inherited_roles_client.create_inherited_role_on_domains_user(
            self.domain['id'], self.user['id'], src_role['id'])

        # List "effective" role assignments from user on the parent project
        params = {'scope.project.id': self.project['id'],
                  'user.id': self.user['id']}
        assignments = self.role_assignments.list_role_assignments(
            effective=True, **params)['role_assignments']
        self.assertNotEmpty(assignments)

        # List "effective" role assignments from user on the leaf project
        params['scope.project.id'] = leaf_project['id']
        assignments = self.role_assignments.list_role_assignments(
            effective=True, **params)['role_assignments']
        self.assertNotEmpty(assignments)

        # Revoke role from domain
        self.inherited_roles_client.delete_inherited_role_from_user_on_domain(
            self.domain['id'], self.user['id'], src_role['id'])

        # List "effective" role assignments from user on the parent project
        # should return an empty list
        params['scope.project.id'] = self.project['id']
        assignments = self.role_assignments.list_role_assignments(
            effective=True, **params)['role_assignments']
        self.assertEmpty(assignments)

        # List "effective" role assignments from user on the leaf project
        # should return an empty list
        params['scope.project.id'] = leaf_project['id']
        assignments = self.role_assignments.list_role_assignments(
            effective=True, **params)['role_assignments']
        self.assertEmpty(assignments)

    @decorators.idempotent_id('9f02ccd9-9b57-46b4-8f77-dd5a736f3a06')
    def test_inherit_assign_list_revoke_user_roles_on_project_tree(self):
        # Create role
        src_role = self.setup_test_role()

        # Create a project hierarchy
        leaf_project = self.setup_test_project(domain_id=self.domain['id'],
                                               parent_id=self.project['id'])

        # Assign role on parent project
        self.inherited_roles_client.create_inherited_role_on_projects_user(
            self.project['id'], self.user['id'], src_role['id'])

        # List "effective" role assignments from user on the leaf project
        params = {'scope.project.id': leaf_project['id'],
                  'user.id': self.user['id']}
        assignments = self.role_assignments.list_role_assignments(
            effective=True, **params)['role_assignments']
        self.assertNotEmpty(assignments)

        # Revoke role from parent project
        self.inherited_roles_client.delete_inherited_role_from_user_on_project(
            self.project['id'], self.user['id'], src_role['id'])

        # List "effective" role assignments from user on the leaf project
        # should return an empty list
        assignments = self.role_assignments.list_role_assignments(
            effective=True, **params)['role_assignments']
        self.assertEmpty(assignments)
