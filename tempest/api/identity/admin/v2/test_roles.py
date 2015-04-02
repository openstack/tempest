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

from six import moves
from tempest_lib.common.utils import data_utils

from tempest.api.identity import base
from tempest import test


class RolesTestJSON(base.BaseIdentityV2AdminTest):

    @classmethod
    def resource_setup(cls):
        super(RolesTestJSON, cls).resource_setup()
        for _ in moves.xrange(5):
            role_name = data_utils.rand_name(name='role')
            role = cls.client.create_role(role_name)
            cls.data.roles.append(role)

    def _get_role_params(self):
        self.data.setup_test_user()
        self.data.setup_test_role()
        user = self.get_user_by_name(self.data.test_user)
        tenant = self.get_tenant_by_name(self.data.test_tenant)
        role = self.get_role_by_name(self.data.test_role)
        return (user, tenant, role)

    def assert_role_in_role_list(self, role, roles):
        found = False
        for user_role in roles:
            if user_role['id'] == role['id']:
                found = True
        self.assertTrue(found, "assigned role was not in list")

    @test.attr(type='gate')
    @test.idempotent_id('75d9593f-50b7-4fcf-bd64-e3fb4a278e23')
    def test_list_roles(self):
        """Return a list of all roles."""
        body = self.client.list_roles()
        found = [role for role in body if role in self.data.roles]
        self.assertTrue(any(found))
        self.assertEqual(len(found), len(self.data.roles))

    @test.attr(type='gate')
    @test.idempotent_id('c62d909d-6c21-48c0-ae40-0a0760e6db5e')
    def test_role_create_delete(self):
        """Role should be created, verified, and deleted."""
        role_name = data_utils.rand_name(name='role-test')
        body = self.client.create_role(role_name)
        self.assertEqual(role_name, body['name'])

        body = self.client.list_roles()
        found = [role for role in body if role['name'] == role_name]
        self.assertTrue(any(found))

        body = self.client.delete_role(found[0]['id'])

        body = self.client.list_roles()
        found = [role for role in body if role['name'] == role_name]
        self.assertFalse(any(found))

    @test.attr(type='gate')
    @test.idempotent_id('db6870bd-a6ed-43be-a9b1-2f10a5c9994f')
    def test_get_role_by_id(self):
        """Get a role by its id."""
        self.data.setup_test_role()
        role_id = self.data.role['id']
        role_name = self.data.role['name']
        body = self.client.get_role(role_id)
        self.assertEqual(role_id, body['id'])
        self.assertEqual(role_name, body['name'])

    @test.attr(type='gate')
    @test.idempotent_id('0146f675-ffbd-4208-b3a4-60eb628dbc5e')
    def test_assign_user_role(self):
        """Assign a role to a user on a tenant."""
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        roles = self.client.list_user_roles(tenant['id'], user['id'])
        self.assert_role_in_role_list(role, roles)

    @test.attr(type='gate')
    @test.idempotent_id('f0b9292c-d3ba-4082-aa6c-440489beef69')
    def test_remove_user_role(self):
        """Remove a role assigned to a user on a tenant."""
        (user, tenant, role) = self._get_role_params()
        user_role = self.client.assign_user_role(tenant['id'],
                                                 user['id'], role['id'])
        self.client.remove_user_role(tenant['id'], user['id'],
                                     user_role['id'])

    @test.attr(type='gate')
    @test.idempotent_id('262e1e3e-ed71-4edd-a0e5-d64e83d66d05')
    def test_list_user_roles(self):
        """List roles assigned to a user on tenant."""
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        roles = self.client.list_user_roles(tenant['id'], user['id'])
        self.assert_role_in_role_list(role, roles)
