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

from tempest.api.identity import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class RolesNegativeTestJSON(base.BaseIdentityV2AdminTest):
    """Negative tests of keystone roles via v2 API"""

    def _get_role_params(self):
        user = self.setup_test_user()
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        role = self.setup_test_role()
        return (user, tenant, role)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d5d5f1df-f8ca-4de0-b2ef-259c1cc67025')
    def test_list_roles_by_unauthorized_user(self):
        """Test Non-admin user should not be able to list roles via v2 API"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_roles_client.list_roles)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('11a3c7da-df6c-40c2-abc2-badd682edf9f')
    def test_list_roles_request_without_token(self):
        """Test listing roles without a valid token via v2 API should fail"""
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized, self.roles_client.list_roles)
        self.client.auth_provider.clear_auth()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c0b89e56-accc-4c73-85f8-9c0f866104c1')
    def test_role_create_blank_name(self):
        """Test creating a role with a blank name via v2 API is not allowed"""
        self.assertRaises(lib_exc.BadRequest, self.roles_client.create_role,
                          name='')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('585c8998-a8a4-4641-a5dd-abef7a8ced00')
    def test_create_role_by_unauthorized_user(self):
        """Test non-admin user should not be able to create role via v2 API"""
        role_name = data_utils.rand_name(
            name='role', prefix=CONF.resource_name_prefix)
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_roles_client.create_role,
                          name=role_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a7edd17a-e34a-4aab-8bb7-fa6f498645b8')
    def test_create_role_request_without_token(self):
        """Test creating role without a valid token via v2 API should fail"""
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        role_name = data_utils.rand_name(
            name='role', prefix=CONF.resource_name_prefix)
        self.assertRaises(lib_exc.Unauthorized,
                          self.roles_client.create_role, name=role_name)
        self.client.auth_provider.clear_auth()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c0cde2c8-81c1-4bb0-8fe2-cf615a3547a8')
    def test_role_create_duplicate(self):
        """Test role names should be unique via v2 API"""
        role_name = data_utils.rand_name(
            name='role-dup', prefix=CONF.resource_name_prefix)
        body = self.roles_client.create_role(name=role_name)['role']
        role1_id = body.get('id')
        self.addCleanup(self.roles_client.delete_role, role1_id)
        self.assertRaises(lib_exc.Conflict, self.roles_client.create_role,
                          name=role_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('15347635-b5b1-4a87-a280-deb2bd6d865e')
    def test_delete_role_by_unauthorized_user(self):
        """Test non-admin user should not be able to delete role via v2 API"""
        role_name = data_utils.rand_name(
            name='role', prefix=CONF.resource_name_prefix)
        body = self.roles_client.create_role(name=role_name)['role']
        self.addCleanup(self.roles_client.delete_role, body['id'])
        role_id = body.get('id')
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_roles_client.delete_role, role_id)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('44b60b20-70de-4dac-beaf-a3fc2650a16b')
    def test_delete_role_request_without_token(self):
        """Test deleting role without a valid token via v2 API should fail"""
        role_name = data_utils.rand_name(
            name='role', prefix=CONF.resource_name_prefix)
        body = self.roles_client.create_role(name=role_name)['role']
        self.addCleanup(self.roles_client.delete_role, body['id'])
        role_id = body.get('id')
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized,
                          self.roles_client.delete_role,
                          role_id)
        self.client.auth_provider.clear_auth()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('38373691-8551-453a-b074-4260ad8298ef')
    def test_delete_role_non_existent(self):
        """Test deleting a non existent role via v2 API should fail"""
        non_existent_role = data_utils.rand_uuid_hex()
        self.assertRaises(lib_exc.NotFound, self.roles_client.delete_role,
                          non_existent_role)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('391df5cf-3ec3-46c9-bbe5-5cb58dd4dc41')
    def test_assign_user_role_by_unauthorized_user(self):
        """Test non-admin user assigning a role to user via v2 API

        Non-admin user should not be authorized to assign a role to user via
        v2 API.
        """
        (user, tenant, role) = self._get_role_params()
        self.assertRaises(
            lib_exc.Forbidden,
            self.non_admin_roles_client.create_user_role_on_project,
            tenant['id'], user['id'], role['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f0d2683c-5603-4aee-95d7-21420e87cfd8')
    def test_assign_user_role_request_without_token(self):
        """Test assigning a role to a user without a valid token via v2 API

        Assigning a role to a user without a valid token via v2 API should
        fail.
        """
        (user, tenant, role) = self._get_role_params()
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(
            lib_exc.Unauthorized,
            self.roles_client.create_user_role_on_project, tenant['id'],
            user['id'], role['id'])
        self.client.auth_provider.clear_auth()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('99b297f6-2b5d-47c7-97a9-8b6bb4f91042')
    def test_assign_user_role_for_non_existent_role(self):
        """Test assigning a non existent role to user via v2 API

        Assigning a non existent role to user via v2 API should fail.
        """
        (user, tenant, _) = self._get_role_params()
        non_existent_role = data_utils.rand_uuid_hex()
        self.assertRaises(lib_exc.NotFound,
                          self.roles_client.create_user_role_on_project,
                          tenant['id'], user['id'], non_existent_role)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b2285aaa-9e76-4704-93a9-7a8acd0a6c8f')
    def test_assign_user_role_for_non_existent_tenant(self):
        """Test assigning a role on a non existent tenant via v2 API

        Assigning a role on a non existent tenant via v2 API should fail.
        """
        (user, _, role) = self._get_role_params()
        non_existent_tenant = data_utils.rand_uuid_hex()
        self.assertRaises(lib_exc.NotFound,
                          self.roles_client.create_user_role_on_project,
                          non_existent_tenant, user['id'], role['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5c3132cd-c4c8-4402-b5ea-71eb44e97793')
    def test_assign_duplicate_user_role(self):
        """Test duplicate user role should not get assigned via v2 API"""
        (user, tenant, role) = self._get_role_params()
        self.roles_client.create_user_role_on_project(tenant['id'],
                                                      user['id'],
                                                      role['id'])
        self.assertRaises(lib_exc.Conflict,
                          self.roles_client.create_user_role_on_project,
                          tenant['id'], user['id'], role['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d0537987-0977-448f-a435-904c15de7298')
    def test_remove_user_role_by_unauthorized_user(self):
        """Test non-admin user removing a user's role via v2 API

        Non-admin user should not be authorized to remove a user's role via
        v2 API
        """
        (user, tenant, role) = self._get_role_params()
        self.roles_client.create_user_role_on_project(tenant['id'],
                                                      user['id'],
                                                      role['id'])
        self.assertRaises(
            lib_exc.Forbidden,
            self.non_admin_roles_client.delete_role_from_user_on_project,
            tenant['id'], user['id'], role['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('cac81cf4-c1d2-47dc-90d3-f2b7eb572286')
    def test_remove_user_role_request_without_token(self):
        """Test removing a user's role without a valid token via v2 API

        Removing a user's role without a valid token via v2 API should fail.
        """
        (user, tenant, role) = self._get_role_params()
        self.roles_client.create_user_role_on_project(tenant['id'],
                                                      user['id'],
                                                      role['id'])
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized,
                          self.roles_client.delete_role_from_user_on_project,
                          tenant['id'], user['id'], role['id'])
        self.client.auth_provider.clear_auth()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ab32d759-cd16-41f1-a86e-44405fa9f6d2')
    def test_remove_user_role_non_existent_role(self):
        """Test deleting a non existent role from a user via v2 API

        Deleting a non existent role from a user via v2 API should fail.
        """
        (user, tenant, role) = self._get_role_params()
        self.roles_client.create_user_role_on_project(tenant['id'],
                                                      user['id'],
                                                      role['id'])
        non_existent_role = data_utils.rand_uuid_hex()
        self.assertRaises(lib_exc.NotFound,
                          self.roles_client.delete_role_from_user_on_project,
                          tenant['id'], user['id'], non_existent_role)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('67a679ec-03dd-4551-bbfc-d1c93284f023')
    def test_remove_user_role_non_existent_tenant(self):
        """Test removing a role from a non existent tenant via v2 API

        Removing a role from a non existent tenant via v2 API should fail.
        """
        (user, tenant, role) = self._get_role_params()
        self.roles_client.create_user_role_on_project(tenant['id'],
                                                      user['id'],
                                                      role['id'])
        non_existent_tenant = data_utils.rand_uuid_hex()
        self.assertRaises(lib_exc.NotFound,
                          self.roles_client.delete_role_from_user_on_project,
                          non_existent_tenant, user['id'], role['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7391ab4c-06f3-477a-a64a-c8e55ce89837')
    def test_list_user_roles_by_unauthorized_user(self):
        """Test non-admin user listing a user's roles via v2 API

        Non-admin user should not be authorized to list a user's roles via v2
        API.
        """
        (user, tenant, role) = self._get_role_params()
        self.roles_client.create_user_role_on_project(tenant['id'],
                                                      user['id'],
                                                      role['id'])
        self.assertRaises(
            lib_exc.Forbidden,
            self.non_admin_roles_client.list_user_roles_on_project,
            tenant['id'], user['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('682adfb2-fd5f-4b0a-a9ca-322e9bebb907')
    def test_list_user_roles_request_without_token(self):
        """Test listing user's roles without a valid token via v2 API

        Listing user's roles without a valid token via v2 API should fail
        """
        (user, tenant, _) = self._get_role_params()
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        try:
            self.assertRaises(lib_exc.Unauthorized,
                              self.roles_client.list_user_roles_on_project,
                              tenant['id'],
                              user['id'])
        finally:
            self.client.auth_provider.clear_auth()
