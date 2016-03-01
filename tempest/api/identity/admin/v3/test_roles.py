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
from tempest.common.utils import data_utils
from tempest import test


class RolesV3TestJSON(base.BaseIdentityV3AdminTest):

    @classmethod
    def resource_setup(cls):
        super(RolesV3TestJSON, cls).resource_setup()
        for _ in range(3):
            role_name = data_utils.rand_name(name='role')
            role = cls.roles_client.create_role(name=role_name)['role']
            cls.data.roles.append(role)
        cls.fetched_role_ids = list()
        u_name = data_utils.rand_name('user')
        u_desc = '%s description' % u_name
        u_email = '%s@testmail.tm' % u_name
        cls.u_password = data_utils.rand_password()
        cls.domain = cls.domains_client.create_domain(
            data_utils.rand_name('domain'),
            description=data_utils.rand_name('domain-desc'))['domain']
        cls.project = cls.projects_client.create_project(
            data_utils.rand_name('project'),
            description=data_utils.rand_name('project-desc'),
            domain_id=cls.domain['id'])['project']
        cls.group_body = cls.groups_client.create_group(
            name=data_utils.rand_name('Group'), project_id=cls.project['id'],
            domain_id=cls.domain['id'])['group']
        cls.user_body = cls.users_client.create_user(
            u_name, description=u_desc, password=cls.u_password,
            email=u_email, project_id=cls.project['id'],
            domain_id=cls.domain['id'])['user']
        cls.role = cls.roles_client.create_role(
            name=data_utils.rand_name('Role'))['role']

    @classmethod
    def resource_cleanup(cls):
        cls.roles_client.delete_role(cls.role['id'])
        cls.groups_client.delete_group(cls.group_body['id'])
        cls.users_client.delete_user(cls.user_body['id'])
        cls.projects_client.delete_project(cls.project['id'])
        # NOTE(harika-vakadi): It is necessary to disable the domain
        # before deleting,or else it would result in unauthorized error
        cls.domains_client.update_domain(cls.domain['id'], enabled=False)
        cls.domains_client.delete_domain(cls.domain['id'])
        super(RolesV3TestJSON, cls).resource_cleanup()

    def _list_assertions(self, body, fetched_role_ids, role_id):
        self.assertEqual(len(body), 1)
        self.assertIn(role_id, fetched_role_ids)

    @test.attr(type='smoke')
    @test.idempotent_id('18afc6c0-46cf-4911-824e-9989cc056c3a')
    def test_role_create_update_show_list(self):
        r_name = data_utils.rand_name('Role')
        role = self.roles_client.create_role(name=r_name)['role']
        self.addCleanup(self.roles_client.delete_role, role['id'])
        self.assertIn('name', role)
        self.assertEqual(role['name'], r_name)

        new_name = data_utils.rand_name('NewRole')
        updated_role = self.roles_client.update_role(role['id'],
                                                     name=new_name)['role']
        self.assertIn('name', updated_role)
        self.assertIn('id', updated_role)
        self.assertIn('links', updated_role)
        self.assertNotEqual(r_name, updated_role['name'])

        new_role = self.roles_client.show_role(role['id'])['role']
        self.assertEqual(new_name, new_role['name'])
        self.assertEqual(updated_role['id'], new_role['id'])

        roles = self.roles_client.list_roles()['roles']
        self.assertIn(role['id'], [r['id'] for r in roles])

    @test.idempotent_id('c6b80012-fe4a-498b-9ce8-eb391c05169f')
    def test_grant_list_revoke_role_to_user_on_project(self):
        self.roles_client.assign_user_role_on_project(self.project['id'],
                                                      self.user_body['id'],
                                                      self.role['id'])

        roles = self.roles_client.list_user_roles_on_project(
            self.project['id'], self.user_body['id'])['roles']

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(roles, self.fetched_role_ids,
                              self.role['id'])

        self.roles_client.check_user_role_existence_on_project(
            self.project['id'], self.user_body['id'], self.role['id'])

        self.roles_client.delete_role_from_user_on_project(
            self.project['id'], self.user_body['id'], self.role['id'])

    @test.idempotent_id('6c9a2940-3625-43a3-ac02-5dcec62ef3bd')
    def test_grant_list_revoke_role_to_user_on_domain(self):
        self.roles_client.assign_user_role_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])

        roles = self.roles_client.list_user_roles_on_domain(
            self.domain['id'], self.user_body['id'])['roles']

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(roles, self.fetched_role_ids,
                              self.role['id'])

        self.roles_client.check_user_role_existence_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])

        self.roles_client.delete_role_from_user_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])

    @test.idempotent_id('cbf11737-1904-4690-9613-97bcbb3df1c4')
    def test_grant_list_revoke_role_to_group_on_project(self):
        # Grant role to group on project
        self.roles_client.assign_group_role_on_project(
            self.project['id'], self.group_body['id'], self.role['id'])
        # List group roles on project
        roles = self.roles_client.list_group_roles_on_project(
            self.project['id'], self.group_body['id'])['roles']

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(roles, self.fetched_role_ids,
                              self.role['id'])
        # Add user to group, and insure user has role on project
        self.groups_client.add_group_user(self.group_body['id'],
                                          self.user_body['id'])
        self.addCleanup(self.groups_client.delete_group_user,
                        self.group_body['id'], self.user_body['id'])
        body = self.token.auth(user_id=self.user_body['id'],
                               password=self.u_password,
                               user_domain_name=self.domain['name'],
                               project_name=self.project['name'],
                               project_domain_name=self.domain['name'])
        roles = body['token']['roles']
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0]['id'], self.role['id'])

        self.roles_client.check_role_from_group_on_project_existence(
            self.project['id'], self.group_body['id'], self.role['id'])

        # Revoke role to group on project
        self.roles_client.delete_role_from_group_on_project(
            self.project['id'], self.group_body['id'], self.role['id'])

    @test.idempotent_id('4bf8a70b-e785-413a-ad53-9f91ce02faa7')
    def test_grant_list_revoke_role_to_group_on_domain(self):
        self.roles_client.assign_group_role_on_domain(
            self.domain['id'], self.group_body['id'], self.role['id'])

        roles = self.roles_client.list_group_roles_on_domain(
            self.domain['id'], self.group_body['id'])['roles']

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(roles, self.fetched_role_ids,
                              self.role['id'])

        self.roles_client.check_role_from_group_on_domain_existence(
            self.domain['id'], self.group_body['id'], self.role['id'])

        self.roles_client.delete_role_from_group_on_domain(
            self.domain['id'], self.group_body['id'], self.role['id'])

    @test.idempotent_id('f5654bcc-08c4-4f71-88fe-05d64e06de94')
    def test_list_roles(self):
        # Return a list of all roles
        body = self.roles_client.list_roles()['roles']
        found = [role for role in body if role in self.data.roles]
        self.assertEqual(len(found), len(self.data.roles))
