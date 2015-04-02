# Copyright 2013 Huawei Technologies Co.,LTD.
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

import uuid

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.identity import base
from tempest import test


class RolesNegativeTestJSON(base.BaseIdentityV2AdminTest):

    def _get_role_params(self):
        self.data.setup_test_user()
        self.data.setup_test_role()
        user = self.get_user_by_name(self.data.test_user)
        tenant = self.get_tenant_by_name(self.data.test_tenant)
        role = self.get_role_by_name(self.data.test_role)
        return (user, tenant, role)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('d5d5f1df-f8ca-4de0-b2ef-259c1cc67025')
    def test_list_roles_by_unauthorized_user(self):
        # Non-administrator user should not be able to list roles
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.list_roles)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('11a3c7da-df6c-40c2-abc2-badd682edf9f')
    def test_list_roles_request_without_token(self):
        # Request to list roles without a valid token should fail
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized, self.client.list_roles)
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('c0b89e56-accc-4c73-85f8-9c0f866104c1')
    def test_role_create_blank_name(self):
        # Should not be able to create a role with a blank name
        self.assertRaises(lib_exc.BadRequest, self.client.create_role, '')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('585c8998-a8a4-4641-a5dd-abef7a8ced00')
    def test_create_role_by_unauthorized_user(self):
        # Non-administrator user should not be able to create role
        role_name = data_utils.rand_name(name='role')
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.create_role, role_name)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('a7edd17a-e34a-4aab-8bb7-fa6f498645b8')
    def test_create_role_request_without_token(self):
        # Request to create role without a valid token should fail
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        role_name = data_utils.rand_name(name='role')
        self.assertRaises(lib_exc.Unauthorized,
                          self.client.create_role, role_name)
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('c0cde2c8-81c1-4bb0-8fe2-cf615a3547a8')
    def test_role_create_duplicate(self):
        # Role names should be unique
        role_name = data_utils.rand_name(name='role-dup')
        body = self.client.create_role(role_name)
        role1_id = body.get('id')
        self.addCleanup(self.client.delete_role, role1_id)
        self.assertRaises(lib_exc.Conflict, self.client.create_role,
                          role_name)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('15347635-b5b1-4a87-a280-deb2bd6d865e')
    def test_delete_role_by_unauthorized_user(self):
        # Non-administrator user should not be able to delete role
        role_name = data_utils.rand_name(name='role')
        body = self.client.create_role(role_name)
        self.data.roles.append(body)
        role_id = body.get('id')
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.delete_role, role_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('44b60b20-70de-4dac-beaf-a3fc2650a16b')
    def test_delete_role_request_without_token(self):
        # Request to delete role without a valid token should fail
        role_name = data_utils.rand_name(name='role')
        body = self.client.create_role(role_name)
        self.data.roles.append(body)
        role_id = body.get('id')
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized,
                          self.client.delete_role,
                          role_id)
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('38373691-8551-453a-b074-4260ad8298ef')
    def test_delete_role_non_existent(self):
        # Attempt to delete a non existent role should fail
        non_existent_role = str(uuid.uuid4().hex)
        self.assertRaises(lib_exc.NotFound, self.client.delete_role,
                          non_existent_role)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('391df5cf-3ec3-46c9-bbe5-5cb58dd4dc41')
    def test_assign_user_role_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to
        # assign a role to user
        (user, tenant, role) = self._get_role_params()
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.assign_user_role,
                          tenant['id'], user['id'], role['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f0d2683c-5603-4aee-95d7-21420e87cfd8')
    def test_assign_user_role_request_without_token(self):
        # Request to assign a role to a user without a valid token
        (user, tenant, role) = self._get_role_params()
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized,
                          self.client.assign_user_role, tenant['id'],
                          user['id'], role['id'])
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('99b297f6-2b5d-47c7-97a9-8b6bb4f91042')
    def test_assign_user_role_for_non_existent_role(self):
        # Attempt to assign a non existent role to user should fail
        (user, tenant, role) = self._get_role_params()
        non_existent_role = str(uuid.uuid4().hex)
        self.assertRaises(lib_exc.NotFound, self.client.assign_user_role,
                          tenant['id'], user['id'], non_existent_role)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('b2285aaa-9e76-4704-93a9-7a8acd0a6c8f')
    def test_assign_user_role_for_non_existent_tenant(self):
        # Attempt to assign a role on a non existent tenant should fail
        (user, tenant, role) = self._get_role_params()
        non_existent_tenant = str(uuid.uuid4().hex)
        self.assertRaises(lib_exc.NotFound, self.client.assign_user_role,
                          non_existent_tenant, user['id'], role['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('5c3132cd-c4c8-4402-b5ea-71eb44e97793')
    def test_assign_duplicate_user_role(self):
        # Duplicate user role should not get assigned
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        self.assertRaises(lib_exc.Conflict, self.client.assign_user_role,
                          tenant['id'], user['id'], role['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('d0537987-0977-448f-a435-904c15de7298')
    def test_remove_user_role_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to
        # remove a user's role
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'],
                                     user['id'],
                                     role['id'])
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.remove_user_role,
                          tenant['id'], user['id'], role['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('cac81cf4-c1d2-47dc-90d3-f2b7eb572286')
    def test_remove_user_role_request_without_token(self):
        # Request to remove a user's role without a valid token
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'],
                                     user['id'],
                                     role['id'])
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized,
                          self.client.remove_user_role, tenant['id'],
                          user['id'], role['id'])
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ab32d759-cd16-41f1-a86e-44405fa9f6d2')
    def test_remove_user_role_non_existent_role(self):
        # Attempt to delete a non existent role from a user should fail
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'],
                                     user['id'],
                                     role['id'])
        non_existent_role = str(uuid.uuid4().hex)
        self.assertRaises(lib_exc.NotFound, self.client.remove_user_role,
                          tenant['id'], user['id'], non_existent_role)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('67a679ec-03dd-4551-bbfc-d1c93284f023')
    def test_remove_user_role_non_existent_tenant(self):
        # Attempt to remove a role from a non existent tenant should fail
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'],
                                     user['id'],
                                     role['id'])
        non_existent_tenant = str(uuid.uuid4().hex)
        self.assertRaises(lib_exc.NotFound, self.client.remove_user_role,
                          non_existent_tenant, user['id'], role['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('7391ab4c-06f3-477a-a64a-c8e55ce89837')
    def test_list_user_roles_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to list
        # a user's roles
        (user, tenant, role) = self._get_role_params()
        self.client.assign_user_role(tenant['id'], user['id'], role['id'])
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.list_user_roles, tenant['id'],
                          user['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('682adfb2-fd5f-4b0a-a9ca-322e9bebb907')
    def test_list_user_roles_request_without_token(self):
        # Request to list user's roles without a valid token should fail
        (user, tenant, role) = self._get_role_params()
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        try:
            self.assertRaises(lib_exc.Unauthorized,
                              self.client.list_user_roles, tenant['id'],
                              user['id'])
        finally:
            self.client.auth_provider.clear_auth()
