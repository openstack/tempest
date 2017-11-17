# Copyright 2012 OpenStack Foundation
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
from tempest.lib.common.utils import data_utils
from tempest.lib.common.utils import test_utils
from tempest.lib import decorators


class RolesTestJSON(base.BaseIdentityV2AdminTest):

    @classmethod
    def resource_setup(cls):
        super(RolesTestJSON, cls).resource_setup()
        cls.roles = list()
        for _ in range(5):
            role_name = data_utils.rand_name(name='role')
            role = cls.roles_client.create_role(name=role_name)['role']
            cls.addClassResourceCleanup(
                test_utils.call_and_ignore_notfound_exc,
                cls.roles_client.delete_role, role['id'])
            cls.roles.append(role)

    def _get_role_params(self):
        user = self.setup_test_user()
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        role = self.setup_test_role()
        return (user, tenant, role)

    def assert_role_in_role_list(self, role, roles):
        found = False
        for user_role in roles:
            if user_role['id'] == role['id']:
                found = True
        self.assertTrue(found, "assigned role was not in list")

    @decorators.idempotent_id('75d9593f-50b7-4fcf-bd64-e3fb4a278e23')
    def test_list_roles(self):
        """Return a list of all roles."""
        body = self.roles_client.list_roles()['roles']
        found = [role for role in body if role in self.roles]
        self.assertNotEmpty(found)
        self.assertEqual(len(found), len(self.roles))

    @decorators.idempotent_id('c62d909d-6c21-48c0-ae40-0a0760e6db5e')
    def test_role_create_delete(self):
        """Role should be created, verified, and deleted."""
        role_name = data_utils.rand_name(name='role-test')
        body = self.roles_client.create_role(name=role_name)['role']
        self.addCleanup(test_utils.call_and_ignore_notfound_exc,
                        self.roles_client.delete_role, body['id'])
        self.assertEqual(role_name, body['name'])

        body = self.roles_client.list_roles()['roles']
        found = [role for role in body if role['name'] == role_name]
        self.assertNotEmpty(found)

        body = self.roles_client.delete_role(found[0]['id'])

        body = self.roles_client.list_roles()['roles']
        found = [role for role in body if role['name'] == role_name]
        self.assertEmpty(found)

    @decorators.idempotent_id('db6870bd-a6ed-43be-a9b1-2f10a5c9994f')
    def test_get_role_by_id(self):
        """Get a role by its id."""
        role = self.setup_test_role()
        role_id = role['id']
        role_name = role['name']
        body = self.roles_client.show_role(role_id)['role']
        self.assertEqual(role_id, body['id'])
        self.assertEqual(role_name, body['name'])

    @decorators.idempotent_id('0146f675-ffbd-4208-b3a4-60eb628dbc5e')
    def test_assign_user_role(self):
        """Assign a role to a user on a tenant."""
        (user, tenant, role) = self._get_role_params()
        self.roles_client.create_user_role_on_project(tenant['id'],
                                                      user['id'],
                                                      role['id'])
        roles = self.roles_client.list_user_roles_on_project(
            tenant['id'], user['id'])['roles']
        self.assert_role_in_role_list(role, roles)

    @decorators.idempotent_id('f0b9292c-d3ba-4082-aa6c-440489beef69')
    def test_remove_user_role(self):
        """Remove a role assigned to a user on a tenant."""
        (user, tenant, role) = self._get_role_params()
        user_role = self.roles_client.create_user_role_on_project(
            tenant['id'], user['id'], role['id'])['role']
        self.roles_client.delete_role_from_user_on_project(tenant['id'],
                                                           user['id'],
                                                           user_role['id'])

    @decorators.idempotent_id('262e1e3e-ed71-4edd-a0e5-d64e83d66d05')
    def test_list_user_roles(self):
        """List roles assigned to a user on tenant."""
        (user, tenant, role) = self._get_role_params()
        self.roles_client.create_user_role_on_project(tenant['id'],
                                                      user['id'],
                                                      role['id'])
        roles = self.roles_client.list_user_roles_on_project(
            tenant['id'], user['id'])['roles']
        self.assert_role_in_role_list(role, roles)
