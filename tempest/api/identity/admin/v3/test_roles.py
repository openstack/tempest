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


class RolesV3TestJSON(base.BaseIdentityV3AdminTest):

    @classmethod
    def resource_setup(cls):
        super(RolesV3TestJSON, cls).resource_setup()
        for _ in range(3):
            role_name = data_utils.rand_name(name='role')
            role = cls.client.create_role(role_name)
            cls.data.v3_roles.append(role)
        cls.fetched_role_ids = list()
        u_name = data_utils.rand_name('user')
        u_desc = '%s description' % u_name
        u_email = '%s@testmail.tm' % u_name
        cls.u_password = data_utils.rand_name('pass')
        cls.domain = cls.client.create_domain(
            data_utils.rand_name('domain'),
            description=data_utils.rand_name('domain-desc'))
        cls.project = cls.client.create_project(
            data_utils.rand_name('project'),
            description=data_utils.rand_name('project-desc'),
            domain_id=cls.domain['id'])
        cls.group_body = cls.client.create_group(
            data_utils.rand_name('Group'), project_id=cls.project['id'],
            domain_id=cls.domain['id'])
        cls.user_body = cls.client.create_user(
            u_name, description=u_desc, password=cls.u_password,
            email=u_email, project_id=cls.project['id'],
            domain_id=cls.domain['id'])
        cls.role = cls.client.create_role(
            data_utils.rand_name('Role'))

    @classmethod
    def resource_cleanup(cls):
        cls.client.delete_role(cls.role['id'])
        cls.client.delete_group(cls.group_body['id'])
        cls.client.delete_user(cls.user_body['id'])
        cls.client.delete_project(cls.project['id'])
        # NOTE(harika-vakadi): It is necessary to disable the domain
        # before deleting,or else it would result in unauthorized error
        cls.client.update_domain(cls.domain['id'], enabled=False)
        cls.client.delete_domain(cls.domain['id'])
        super(RolesV3TestJSON, cls).resource_cleanup()

    def _list_assertions(self, body, fetched_role_ids, role_id):
        self.assertEqual(len(body), 1)
        self.assertIn(role_id, fetched_role_ids)

    @test.attr(type='smoke')
    @test.idempotent_id('18afc6c0-46cf-4911-824e-9989cc056c3a')
    def test_role_create_update_get_list(self):
        r_name = data_utils.rand_name('Role')
        role = self.client.create_role(r_name)
        self.addCleanup(self.client.delete_role, role['id'])
        self.assertIn('name', role)
        self.assertEqual(role['name'], r_name)

        new_name = data_utils.rand_name('NewRole')
        updated_role = self.client.update_role(new_name, role['id'])
        self.assertIn('name', updated_role)
        self.assertIn('id', updated_role)
        self.assertIn('links', updated_role)
        self.assertNotEqual(r_name, updated_role['name'])

        new_role = self.client.get_role(role['id'])
        self.assertEqual(new_name, new_role['name'])
        self.assertEqual(updated_role['id'], new_role['id'])

        roles = self.client.list_roles()
        self.assertIn(role['id'], [r['id'] for r in roles])

    @test.attr(type='smoke')
    @test.idempotent_id('c6b80012-fe4a-498b-9ce8-eb391c05169f')
    def test_grant_list_revoke_role_to_user_on_project(self):
        self.client.assign_user_role_on_project(
            self.project['id'], self.user_body['id'], self.role['id'])

        roles = self.client.list_user_roles_on_project(
            self.project['id'], self.user_body['id'])

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(roles, self.fetched_role_ids,
                              self.role['id'])

        self.client.revoke_role_from_user_on_project(
            self.project['id'], self.user_body['id'], self.role['id'])

    @test.attr(type='smoke')
    @test.idempotent_id('6c9a2940-3625-43a3-ac02-5dcec62ef3bd')
    def test_grant_list_revoke_role_to_user_on_domain(self):
        self.client.assign_user_role_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])

        roles = self.client.list_user_roles_on_domain(
            self.domain['id'], self.user_body['id'])

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(roles, self.fetched_role_ids,
                              self.role['id'])

        self.client.revoke_role_from_user_on_domain(
            self.domain['id'], self.user_body['id'], self.role['id'])

    @test.attr(type='smoke')
    @test.idempotent_id('cbf11737-1904-4690-9613-97bcbb3df1c4')
    def test_grant_list_revoke_role_to_group_on_project(self):
        # Grant role to group on project
        self.client.assign_group_role_on_project(
            self.project['id'], self.group_body['id'], self.role['id'])
        # List group roles on project
        roles = self.client.list_group_roles_on_project(
            self.project['id'], self.group_body['id'])

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(roles, self.fetched_role_ids,
                              self.role['id'])
        # Add user to group, and insure user has role on project
        self.client.add_group_user(self.group_body['id'], self.user_body['id'])
        self.addCleanup(self.client.delete_group_user,
                        self.group_body['id'], self.user_body['id'])
        body = self.token.auth(user_id=self.user_body['id'],
                               password=self.u_password,
                               user_domain_name=self.domain['name'],
                               project_name=self.project['name'],
                               project_domain_name=self.domain['name'])
        roles = body['token']['roles']
        self.assertEqual(len(roles), 1)
        self.assertEqual(roles[0]['id'], self.role['id'])
        # Revoke role to group on project
        self.client.revoke_role_from_group_on_project(
            self.project['id'], self.group_body['id'], self.role['id'])

    @test.attr(type='smoke')
    @test.idempotent_id('4bf8a70b-e785-413a-ad53-9f91ce02faa7')
    def test_grant_list_revoke_role_to_group_on_domain(self):
        self.client.assign_group_role_on_domain(
            self.domain['id'], self.group_body['id'], self.role['id'])

        roles = self.client.list_group_roles_on_domain(
            self.domain['id'], self.group_body['id'])

        for i in roles:
            self.fetched_role_ids.append(i['id'])

        self._list_assertions(roles, self.fetched_role_ids,
                              self.role['id'])

        self.client.revoke_role_from_group_on_domain(
            self.domain['id'], self.group_body['id'], self.role['id'])

    @test.attr(type='gate')
    @test.idempotent_id('f5654bcc-08c4-4f71-88fe-05d64e06de94')
    def test_list_roles(self):
        # Return a list of all roles
        body = self.client.list_roles()
        found = [role for role in body if role in self.data.v3_roles]
        self.assertEqual(len(found), len(self.data.v3_roles))
