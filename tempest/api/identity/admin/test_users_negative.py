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
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr
import uuid


class UsersNegativeTestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(UsersNegativeTestJSON, cls).setUpClass()
        cls.alt_user = data_utils.rand_name('test_user_')
        cls.alt_password = data_utils.rand_name('pass_')
        cls.alt_email = cls.alt_user + '@testmail.tm'

    @attr(type=['negative', 'gate'])
    def test_create_user_by_unauthorized_user(self):
        # Non-administrator should not be authorized to create a user
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.create_user, self.alt_user,
                          self.alt_password, self.data.tenant['id'],
                          self.alt_email)

    @attr(type=['negative', 'gate'])
    def test_create_user_with_empty_name(self):
        # User with an empty name should not be created
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.BadRequest, self.client.create_user, '',
                          self.alt_password, self.data.tenant['id'],
                          self.alt_email)

    @attr(type=['negative', 'gate'])
    def test_create_user_with_name_length_over_255(self):
        # Length of user name filed should be restricted to 255 characters
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.BadRequest, self.client.create_user,
                          'a' * 256, self.alt_password,
                          self.data.tenant['id'], self.alt_email)

    @attr(type=['negative', 'gate'])
    def test_create_user_with_duplicate_name(self):
        # Duplicate user should not be created
        self.data.setup_test_user()
        self.assertRaises(exceptions.Conflict, self.client.create_user,
                          self.data.test_user, self.data.test_password,
                          self.data.tenant['id'], self.data.test_email)

    @attr(type=['negative', 'gate'])
    def test_create_user_for_non_existent_tenant(self):
        # Attempt to create a user in a non-existent tenant should fail
        self.assertRaises(exceptions.NotFound, self.client.create_user,
                          self.alt_user, self.alt_password, '49ffgg99999',
                          self.alt_email)

    @attr(type=['negative', 'gate'])
    def test_create_user_request_without_a_token(self):
        # Request to create a user without a valid token should fail
        self.data.setup_test_tenant()
        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.create_user,
                          self.alt_user, self.alt_password,
                          self.data.tenant['id'], self.alt_email)

        # Unset the token to allow further tests to generate a new token
        self.client.auth_provider.clear_auth()

    @attr(type=['negative', 'gate'])
    def test_create_user_with_enabled_non_bool(self):
        # Attempt to create a user with valid enabled para should fail
        self.data.setup_test_tenant()
        name = data_utils.rand_name('test_user_')
        self.assertRaises(exceptions.BadRequest, self.client.create_user,
                          name, self.alt_password,
                          self.data.tenant['id'],
                          self.alt_email, enabled=3)

    @attr(type=['negative', 'gate'])
    def test_update_user_for_non_existent_user(self):
        # Attempt to update a user non-existent user should fail
        user_name = data_utils.rand_name('user-')
        non_existent_id = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound, self.client.update_user,
                          non_existent_id, name=user_name)

    @attr(type=['negative', 'gate'])
    def test_update_user_request_without_a_token(self):
        # Request to update a user without a valid token should fail

        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.update_user,
                          self.alt_user)

        # Unset the token to allow further tests to generate a new token
        self.client.auth_provider.clear_auth()

    @attr(type=['negative', 'gate'])
    def test_update_user_by_unauthorized_user(self):
        # Non-administrator should not be authorized to update user
        self.data.setup_test_tenant()
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.update_user, self.alt_user)

    @attr(type=['negative', 'gate'])
    def test_delete_users_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to delete a user
        self.data.setup_test_user()
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.delete_user,
                          self.data.user['id'])

    @attr(type=['negative', 'gate'])
    def test_delete_non_existent_user(self):
        # Attempt to delete a non-existent user should fail
        self.assertRaises(exceptions.NotFound, self.client.delete_user,
                          'junk12345123')

    @attr(type=['negative', 'gate'])
    def test_delete_user_request_without_a_token(self):
        # Request to delete a user without a valid token should fail

        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.delete_user,
                          self.alt_user)

        # Unset the token to allow further tests to generate a new token
        self.client.auth_provider.clear_auth()

    @attr(type=['negative', 'gate'])
    def test_authentication_for_disabled_user(self):
        # Disabled user's token should not get authenticated
        self.data.setup_test_user()
        self.disable_user(self.data.test_user)
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          self.data.test_user,
                          self.data.test_password,
                          self.data.test_tenant)

    @attr(type=['negative', 'gate'])
    def test_authentication_when_tenant_is_disabled(self):
        # User's token for a disabled tenant should not be authenticated
        self.data.setup_test_user()
        self.disable_tenant(self.data.test_tenant)
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          self.data.test_user,
                          self.data.test_password,
                          self.data.test_tenant)

    @attr(type=['negative', 'gate'])
    def test_authentication_with_invalid_tenant(self):
        # User's token for an invalid tenant should not be authenticated
        self.data.setup_test_user()
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          self.data.test_user,
                          self.data.test_password,
                          'junktenant1234')

    @attr(type=['negative', 'gate'])
    def test_authentication_with_invalid_username(self):
        # Non-existent user's token should not get authenticated
        self.data.setup_test_user()
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          'junkuser123', self.data.test_password,
                          self.data.test_tenant)

    @attr(type=['negative', 'gate'])
    def test_authentication_with_invalid_password(self):
        # User's token with invalid password should not be authenticated
        self.data.setup_test_user()
        self.assertRaises(exceptions.Unauthorized, self.token_client.auth,
                          self.data.test_user, 'junkpass1234',
                          self.data.test_tenant)

    @attr(type=['negative', 'gate'])
    def test_get_users_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to get user list
        self.data.setup_test_user()
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.get_users)

    @attr(type=['negative', 'gate'])
    def test_get_users_request_without_token(self):
        # Request to get list of users without a valid token should fail
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.get_users)
        self.client.auth_provider.clear_auth()

    @attr(type=['negative', 'gate'])
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
            self.assertRaises(exceptions.NotFound,
                              self.client.list_users_for_tenant, invalid)


class UsersNegativeTestXML(UsersNegativeTestJSON):
    _interface = 'xml'
