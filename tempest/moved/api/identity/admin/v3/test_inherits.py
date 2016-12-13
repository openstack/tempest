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
from tempest import config
from tempest import test

CONF = config.CONF


class BaseInheritsV3Test(base.BaseIdentityV3AdminTest):

    @classmethod
    def skip_checks(cls):
        super(BaseInheritsV3Test, cls).skip_checks()
        if not test.is_extension_enabled('OS-INHERIT', 'identity'):
            raise cls.skipException("Inherits aren't enabled")

    @classmethod
    def resource_setup(cls):
        super(BaseInheritsV3Test, cls).resource_setup()
        u_name = data_utils.rand_name('user-')
        u_desc = '%s description' % u_name
        u_email = '%s@testmail.tm' % u_name
        u_password = data_utils.rand_name('pass-')
        cls.domain = cls.domains_client.create_domain(
            data_utils.rand_name('domain-'),
            description=data_utils.rand_name('domain-desc-'))['domain']
        cls.project = cls.projects_client.create_project(
            data_utils.rand_name('project-'),
            description=data_utils.rand_name('project-desc-'),
            domain_id=cls.domain['id'])['project']
        cls.group = cls.groups_client.create_group(
            name=data_utils.rand_name('group-'), project_id=cls.project['id'],
            domain_id=cls.domain['id'])['group']
        cls.user = cls.users_client.create_user(
            u_name, description=u_desc, password=u_password,
            email=u_email, project_id=cls.project['id'],
            domain_id=cls.domain['id'])['user']

    @classmethod
    def resource_cleanup(cls):
        cls.groups_client.delete_group(cls.group['id'])
        cls.users_client.delete_user(cls.user['id'])
        cls.projects_client.delete_project(cls.project['id'])
        cls.domains_client.update_domain(cls.domain['id'], enabled=False)
        cls.domains_client.delete_domain(cls.domain['id'])
        super(BaseInheritsV3Test, cls).resource_cleanup()

    def _list_assertions(self, body, fetched_role_ids, role_id):
        self.assertEqual(len(body), 1)
        self.assertIn(role_id, fetched_role_ids)


class InheritsV3TestJSON(BaseInheritsV3Test):

    @test.idempotent_id('4e6f0366-97c8-423c-b2be-41eae6ac91c8')
    def test_inherit_assign_list_check_revoke_roles_on_domains_user(self):
        # Create role
        src_role = self.roles_client.create_role(
            name=data_utils.rand_name('Role'))['role']
        self.addCleanup(self.roles_client.delete_role, src_role['id'])
        # Assign role on domains user
        self.roles_client.assign_inherited_role_on_domains_user(
            self.domain['id'], self.user['id'], src_role['id'])
        # list role on domains user
        roles = self.roles_client.\
            list_inherited_project_role_for_user_on_domain(
                self.domain['id'], self.user['id'])['roles']

        fetched_role_ids = [i['id'] for i in roles]
        self._list_assertions(roles, fetched_role_ids,
                              src_role['id'])

        # Check role on domains user
        self.roles_client.check_user_inherited_project_role_on_domain(
            self.domain['id'], self.user['id'], src_role['id'])
        # Revoke role from domains user.
        self.roles_client.revoke_inherited_role_from_user_on_domain(
            self.domain['id'], self.user['id'], src_role['id'])

    @test.idempotent_id('c7a8dda2-be50-4fb4-9a9c-e830771078b1')
    def test_inherit_assign_list_check_revoke_roles_on_domains_group(self):
        # Create role
        src_role = self.roles_client.create_role(
            name=data_utils.rand_name('Role'))['role']
        self.addCleanup(self.roles_client.delete_role, src_role['id'])
        # Assign role on domains group
        self.roles_client.assign_inherited_role_on_domains_group(
            self.domain['id'], self.group['id'], src_role['id'])
        # List role on domains group
        roles = self.roles_client.\
            list_inherited_project_role_for_group_on_domain(
                self.domain['id'], self.group['id'])['roles']

        fetched_role_ids = [i['id'] for i in roles]
        self._list_assertions(roles, fetched_role_ids,
                              src_role['id'])

        # Check role on domains group
        self.roles_client.check_group_inherited_project_role_on_domain(
            self.domain['id'], self.group['id'], src_role['id'])
        # Revoke role from domains group
        self.roles_client.revoke_inherited_role_from_group_on_domain(
            self.domain['id'], self.group['id'], src_role['id'])

    @test.idempotent_id('18b70e45-7687-4b72-8277-b8f1a47d7591')
    def test_inherit_assign_check_revoke_roles_on_projects_user(self):
        # Create role
        src_role = self.roles_client.create_role(
            name=data_utils.rand_name('Role'))['role']
        self.addCleanup(self.roles_client.delete_role, src_role['id'])
        # Assign role on projects user
        self.roles_client.assign_inherited_role_on_projects_user(
            self.project['id'], self.user['id'], src_role['id'])
        # Check role on projects user
        self.roles_client.check_user_has_flag_on_inherited_to_project(
            self.project['id'], self.user['id'], src_role['id'])
        # Revoke role from projects user
        self.roles_client.revoke_inherited_role_from_user_on_project(
            self.project['id'], self.user['id'], src_role['id'])

    @test.idempotent_id('26021436-d5a4-4256-943c-ded01e0d4b45')
    def test_inherit_assign_check_revoke_roles_on_projects_group(self):
        # Create role
        src_role = self.roles_client.create_role(
            name=data_utils.rand_name('Role'))['role']
        self.addCleanup(self.roles_client.delete_role, src_role['id'])
        # Assign role on projects group
        self.roles_client.assign_inherited_role_on_projects_group(
            self.project['id'], self.group['id'], src_role['id'])
        # Check role on projects group
        self.roles_client.check_group_has_flag_on_inherited_to_project(
            self.project['id'], self.group['id'], src_role['id'])
        # Revoke role from projects group
        self.roles_client.revoke_inherited_role_from_group_on_project(
            self.project['id'], self.group['id'], src_role['id'])
