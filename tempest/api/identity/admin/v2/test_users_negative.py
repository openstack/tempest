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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class UsersNegativeTestJSON(base.BaseIdentityV2AdminTest):
    """Negative tests of identity users via v2 API"""

    @classmethod
    def resource_setup(cls):
        super(UsersNegativeTestJSON, cls).resource_setup()
        cls.alt_user = data_utils.rand_name('test_user')
        cls.alt_password = data_utils.rand_password()
        cls.alt_email = cls.alt_user + '@testmail.tm'

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('60a1f5fa-5744-4cdf-82bf-60b7de2d29a4')
    def test_create_user_by_unauthorized_user(self):
        """Non-admin should not be authorized to create a user via v2 API"""
        tenant = self.setup_test_tenant()
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_users_client.create_user,
                          name=self.alt_user, password=self.alt_password,
                          tenantId=tenant['id'],
                          email=self.alt_email)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d80d0c2f-4514-4d1e-806d-0930dfc5a187')
    def test_create_user_with_empty_name(self):
        """User with an empty name should not be created via v2 API"""
        tenant = self.setup_test_tenant()
        self.assertRaises(lib_exc.BadRequest, self.users_client.create_user,
                          name='', password=self.alt_password,
                          tenantId=tenant['id'],
                          email=self.alt_email)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7704b4f3-3b75-4b82-87cc-931d41c8f780')
    def test_create_user_with_name_length_over_255(self):
        """Length of user name should not exceed 255 via v2 API"""
        tenant = self.setup_test_tenant()
        self.assertRaises(lib_exc.BadRequest, self.users_client.create_user,
                          name='a' * 256, password=self.alt_password,
                          tenantId=tenant['id'],
                          email=self.alt_email)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('57ae8558-120c-4723-9308-3751474e7ecf')
    def test_create_user_with_duplicate_name(self):
        """Duplicate user should not be created via v2 API"""
        password = data_utils.rand_password()
        user = self.setup_test_user(password)
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        self.assertRaises(lib_exc.Conflict, self.users_client.create_user,
                          name=user['name'],
                          password=password,
                          tenantId=tenant['id'],
                          email=user['email'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('0132cc22-7c4f-42e1-9e50-ac6aad31d59a')
    def test_create_user_for_non_existent_tenant(self):
        """Creating a user in a non-existent tenant via v2 API should fail"""
        self.assertRaises(lib_exc.NotFound, self.users_client.create_user,
                          name=self.alt_user,
                          password=self.alt_password,
                          tenantId='49ffgg99999',
                          email=self.alt_email)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('55bbb103-d1ae-437b-989b-bcdf8175c1f4')
    def test_create_user_request_without_a_token(self):
        """Creating a user without a valid token via v2 API should fail"""
        tenant = self.setup_test_tenant()
        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)

        # Unset the token to allow further tests to generate a new token
        self.addCleanup(self.client.auth_provider.clear_auth)

        self.assertRaises(lib_exc.Unauthorized, self.users_client.create_user,
                          name=self.alt_user, password=self.alt_password,
                          tenantId=tenant['id'],
                          email=self.alt_email)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('23a2f3da-4a1a-41da-abdd-632328a861ad')
    def test_create_user_with_enabled_non_bool(self):
        """Creating a user with invalid enabled para via v2 API should fail"""
        tenant = self.setup_test_tenant()
        name = data_utils.rand_name('test_user')
        self.assertRaises(lib_exc.BadRequest, self.users_client.create_user,
                          name=name, password=self.alt_password,
                          tenantId=tenant['id'],
                          email=self.alt_email, enabled=3)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('3d07e294-27a0-4144-b780-a2a1bf6fee19')
    def test_update_user_for_non_existent_user(self):
        """Updating a non-existent user via v2 API should fail"""
        user_name = data_utils.rand_name('user')
        non_existent_id = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.users_client.update_user,
                          non_existent_id, name=user_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('3cc2a64b-83aa-4b02-88f0-d6ab737c4466')
    def test_update_user_request_without_a_token(self):
        """Updating a user without a valid token via v2 API should fail"""

        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)

        # Unset the token to allow further tests to generate a new token
        self.addCleanup(self.client.auth_provider.clear_auth)

        self.assertRaises(lib_exc.Unauthorized, self.users_client.update_user,
                          self.alt_user)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('424868d5-18a7-43e1-8903-a64f95ee3aac')
    def test_update_user_by_unauthorized_user(self):
        """Non-admin should not be authorized to update user via v2 API"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_users_client.update_user,
                          self.alt_user)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d45195d5-33ed-41b9-a452-7d0d6a00f6e9')
    def test_delete_users_by_unauthorized_user(self):
        """Non-admin should not be authorized to delete a user via v2 API"""
        user = self.setup_test_user()
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_users_client.delete_user,
                          user['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7cc82f7e-9998-4f89-abae-23df36495867')
    def test_delete_non_existent_user(self):
        """Attempt to delete a non-existent user via v2 API should fail"""
        self.assertRaises(lib_exc.NotFound, self.users_client.delete_user,
                          'junk12345123')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('57fe1df8-0aa7-46c0-ae9f-c2e785c7504a')
    def test_delete_user_request_without_a_token(self):
        """Deleting a user without a valid token via v2 API should fail"""

        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)

        # Unset the token to allow further tests to generate a new token
        self.addCleanup(self.client.auth_provider.clear_auth)

        self.assertRaises(lib_exc.Unauthorized, self.users_client.delete_user,
                          self.alt_user)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('593a4981-f6d4-460a-99a1-57a78bf20829')
    def test_authentication_for_disabled_user(self):
        """Disabled user's token should not get authenticated via v2 API"""
        password = data_utils.rand_password()
        user = self.setup_test_user(password)
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        self.disable_user(user['name'])
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          user['name'],
                          password,
                          tenant['name'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('440a7a8d-9328-4b7b-83e0-d717010495e4')
    def test_authentication_when_tenant_is_disabled(self):
        """Test User's token for a disabled tenant via v2 API

        User's token for a disabled tenant should not be authenticated via
        v2 API.
        """
        password = data_utils.rand_password()
        user = self.setup_test_user(password)
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        self.disable_tenant(tenant['name'])
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          user['name'],
                          password,
                          tenant['name'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('921f1ad6-7907-40b8-853f-637e7ee52178')
    def test_authentication_with_invalid_tenant(self):
        """Test User's token for an invalid tenant via v2 API

        User's token for an invalid tenant should not be authenticated via V2
        API.
        """
        password = data_utils.rand_password()
        user = self.setup_test_user(password)
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          user['name'],
                          password,
                          'junktenant1234')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('bde9aecd-3b1c-4079-858f-beb5deaa5b5e')
    def test_authentication_with_invalid_username(self):
        """Non-existent user's token should not get authorized via v2 API"""
        password = data_utils.rand_password()
        user = self.setup_test_user(password)
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          'junkuser123', password, tenant['name'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d5308b33-3574-43c3-8d87-1c090c5e1eca')
    def test_authentication_with_invalid_password(self):
        """Test User's token with invalid password via v2 API

        User's token with invalid password should not be authenticated via V2
        API.
        """
        user = self.setup_test_user()
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          user['name'], 'junkpass1234', tenant['name'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('284192ce-fb7c-4909-a63b-9a502e0ddd11')
    def test_get_users_by_unauthorized_user(self):
        """Non-admin should not be authorized to get user list via v2 API"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_users_client.list_users)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a73591ec-1903-4ffe-be42-282b39fefc9d')
    def test_get_users_request_without_token(self):
        """Listing users without a valid token via v2 API should fail"""
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)

        # Unset the token to allow further tests to generate a new token
        self.addCleanup(self.client.auth_provider.clear_auth)

        self.assertRaises(lib_exc.Unauthorized, self.users_client.list_users)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('f5d39046-fc5f-425c-b29e-bac2632da28e')
    def test_list_users_with_invalid_tenant(self):
        """Listing users for a non-existent tenant via v2 API should fail"""
        # Assign invalid tenant ids
        invalid_id = list()
        invalid_id.append(data_utils.rand_name('999'))
        invalid_id.append('alpha')
        invalid_id.append(data_utils.rand_name("dddd@#%%^$"))
        invalid_id.append('!@#()$%^&*?<>{}[]')
        # List the users with invalid tenant id
        for invalid in invalid_id:
            self.assertRaises(lib_exc.NotFound,
                              self.tenants_client.list_tenant_users, invalid)
