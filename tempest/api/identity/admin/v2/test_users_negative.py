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

import uuid

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.identity import base
from tempest import test


class UsersNegativeTestJSON(base.BaseIdentityV2AdminTest):

    @classmethod
    def resource_setup(cls):
        super(UsersNegativeTestJSON, cls).resource_setup()
        cls.alt_user = data_utils.rand_name('test_user')
        cls.alt_password = data_utils.rand_name('pass')
        cls.alt_email = cls.alt_user + '@testmail.tm'

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('60a1f5fa-5744-4cdf-82bf-60b7de2d29a4')
    def test_create_user_by_unauthorized_user(self):
        # Non-administrator should not be authorized to create a user
        self.data.setup_test_tenant()
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.create_user, self.alt_user,
                          self.alt_password, self.data.tenant['id'],
                          self.alt_email)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('d80d0c2f-4514-4d1e-806d-0930dfc5a187')
    def test_create_user_with_empty_name(self):
        # User with an empty name should not be created
        self.data.setup_test_tenant()
        self.assertRaises(lib_exc.BadRequest, self.client.create_user, '',
                          self.alt_password, self.data.tenant['id'],
                          self.alt_email)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('7704b4f3-3b75-4b82-87cc-931d41c8f780')
    def test_create_user_with_name_length_over_255(self):
        # Length of user name filed should be restricted to 255 characters
        self.data.setup_test_tenant()
        self.assertRaises(lib_exc.BadRequest, self.client.create_user,
                          'a' * 256, self.alt_password,
                          self.data.tenant['id'], self.alt_email)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('57ae8558-120c-4723-9308-3751474e7ecf')
    def test_create_user_with_duplicate_name(self):
        # Duplicate user should not be created
        self.data.setup_test_user()
        self.assertRaises(lib_exc.Conflict, self.client.create_user,
                          self.data.test_user, self.data.test_password,
                          self.data.tenant['id'], self.data.test_email)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('0132cc22-7c4f-42e1-9e50-ac6aad31d59a')
    def test_create_user_for_non_existent_tenant(self):
        # Attempt to create a user in a non-existent tenant should fail
        self.assertRaises(lib_exc.NotFound, self.client.create_user,
                          self.alt_user, self.alt_password, '49ffgg99999',
                          self.alt_email)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('55bbb103-d1ae-437b-989b-bcdf8175c1f4')
    def test_create_user_request_without_a_token(self):
        # Request to create a user without a valid token should fail
        self.data.setup_test_tenant()
        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized, self.client.create_user,
                          self.alt_user, self.alt_password,
                          self.data.tenant['id'], self.alt_email)

        # Unset the token to allow further tests to generate a new token
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('23a2f3da-4a1a-41da-abdd-632328a861ad')
    def test_create_user_with_enabled_non_bool(self):
        # Attempt to create a user with valid enabled para should fail
        self.data.setup_test_tenant()
        name = data_utils.rand_name('test_user')
        self.assertRaises(lib_exc.BadRequest, self.client.create_user,
                          name, self.alt_password,
                          self.data.tenant['id'],
                          self.alt_email, enabled=3)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('3d07e294-27a0-4144-b780-a2a1bf6fee19')
    def test_update_user_for_non_existent_user(self):
        # Attempt to update a user non-existent user should fail
        user_name = data_utils.rand_name('user')
        non_existent_id = str(uuid.uuid4())
        self.assertRaises(lib_exc.NotFound, self.client.update_user,
                          non_existent_id, name=user_name)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('3cc2a64b-83aa-4b02-88f0-d6ab737c4466')
    def test_update_user_request_without_a_token(self):
        # Request to update a user without a valid token should fail

        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized, self.client.update_user,
                          self.alt_user)

        # Unset the token to allow further tests to generate a new token
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('424868d5-18a7-43e1-8903-a64f95ee3aac')
    def test_update_user_by_unauthorized_user(self):
        # Non-administrator should not be authorized to update user
        self.data.setup_test_tenant()
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.update_user, self.alt_user)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('d45195d5-33ed-41b9-a452-7d0d6a00f6e9')
    def test_delete_users_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to delete a user
        self.data.setup_test_user()
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.delete_user,
                          self.data.user['id'])

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('7cc82f7e-9998-4f89-abae-23df36495867')
    def test_delete_non_existent_user(self):
        # Attempt to delete a non-existent user should fail
        self.assertRaises(lib_exc.NotFound, self.client.delete_user,
                          'junk12345123')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('57fe1df8-0aa7-46c0-ae9f-c2e785c7504a')
    def test_delete_user_request_without_a_token(self):
        # Request to delete a user without a valid token should fail

        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized, self.client.delete_user,
                          self.alt_user)

        # Unset the token to allow further tests to generate a new token
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('593a4981-f6d4-460a-99a1-57a78bf20829')
    def test_authentication_for_disabled_user(self):
        # Disabled user's token should not get authenticated
        self.data.setup_test_user()
        self.disable_user(self.data.test_user)
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          self.data.test_user,
                          self.data.test_password,
                          self.data.test_tenant)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('440a7a8d-9328-4b7b-83e0-d717010495e4')
    def test_authentication_when_tenant_is_disabled(self):
        # User's token for a disabled tenant should not be authenticated
        self.data.setup_test_user()
        self.disable_tenant(self.data.test_tenant)
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          self.data.test_user,
                          self.data.test_password,
                          self.data.test_tenant)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('921f1ad6-7907-40b8-853f-637e7ee52178')
    def test_authentication_with_invalid_tenant(self):
        # User's token for an invalid tenant should not be authenticated
        self.data.setup_test_user()
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          self.data.test_user,
                          self.data.test_password,
                          'junktenant1234')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('bde9aecd-3b1c-4079-858f-beb5deaa5b5e')
    def test_authentication_with_invalid_username(self):
        # Non-existent user's token should not get authenticated
        self.data.setup_test_user()
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          'junkuser123', self.data.test_password,
                          self.data.test_tenant)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('d5308b33-3574-43c3-8d87-1c090c5e1eca')
    def test_authentication_with_invalid_password(self):
        # User's token with invalid password should not be authenticated
        self.data.setup_test_user()
        self.assertRaises(lib_exc.Unauthorized, self.token_client.auth,
                          self.data.test_user, 'junkpass1234',
                          self.data.test_tenant)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('284192ce-fb7c-4909-a63b-9a502e0ddd11')
    def test_get_users_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to get user list
        self.data.setup_test_user()
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_client.get_users)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('a73591ec-1903-4ffe-be42-282b39fefc9d')
    def test_get_users_request_without_token(self):
        # Request to get list of users without a valid token should fail
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized, self.client.get_users)
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f5d39046-fc5f-425c-b29e-bac2632da28e')
    def test_list_users_with_invalid_tenant(self):
        # Should not be able to return a list of all
        # users for a non-existent tenant
        # Assign invalid tenant ids
        invalid_id = list()
        invalid_id.append(data_utils.rand_name('999'))
        invalid_id.append('alpha')
        invalid_id.append(data_utils.rand_name("dddd@#%%^$"))
        invalid_id.append('!@#()$%^&*?<>{}[]')
        # List the users with invalid tenant id
        for invalid in invalid_id:
            self.assertRaises(lib_exc.NotFound,
                              self.client.list_users_for_tenant, invalid)
