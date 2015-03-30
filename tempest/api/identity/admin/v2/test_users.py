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

from tempest_lib.common.utils import data_utils
from testtools import matchers

from tempest.api.identity import base
from tempest import test


class UsersTestJSON(base.BaseIdentityV2AdminTest):

    @classmethod
    def resource_setup(cls):
        super(UsersTestJSON, cls).resource_setup()
        cls.alt_user = data_utils.rand_name('test_user')
        cls.alt_password = data_utils.rand_name('pass')
        cls.alt_email = cls.alt_user + '@testmail.tm'

    @test.attr(type='smoke')
    @test.idempotent_id('2d55a71e-da1d-4b43-9c03-d269fd93d905')
    def test_create_user(self):
        # Create a user
        self.data.setup_test_tenant()
        user = self.client.create_user(self.alt_user, self.alt_password,
                                       self.data.tenant['id'],
                                       self.alt_email)
        self.data.users.append(user)
        self.assertEqual(self.alt_user, user['name'])

    @test.attr(type='smoke')
    @test.idempotent_id('89d9fdb8-15c2-4304-a429-48715d0af33d')
    def test_create_user_with_enabled(self):
        # Create a user with enabled : False
        self.data.setup_test_tenant()
        name = data_utils.rand_name('test_user')
        user = self.client.create_user(name, self.alt_password,
                                       self.data.tenant['id'],
                                       self.alt_email, enabled=False)
        self.data.users.append(user)
        self.assertEqual(name, user['name'])
        self.assertEqual('false', str(user['enabled']).lower())
        self.assertEqual(self.alt_email, user['email'])

    @test.attr(type='smoke')
    @test.idempotent_id('39d05857-e8a5-4ed4-ba83-0b52d3ab97ee')
    def test_update_user(self):
        # Test case to check if updating of user attributes is successful.
        test_user = data_utils.rand_name('test_user')
        self.data.setup_test_tenant()
        user = self.client.create_user(test_user, self.alt_password,
                                       self.data.tenant['id'],
                                       self.alt_email)
        # Delete the User at the end of this method
        self.addCleanup(self.client.delete_user, user['id'])
        # Updating user details with new values
        u_name2 = data_utils.rand_name('user2')
        u_email2 = u_name2 + '@testmail.tm'
        update_user = self.client.update_user(user['id'], name=u_name2,
                                              email=u_email2,
                                              enabled=False)
        self.assertEqual(u_name2, update_user['name'])
        self.assertEqual(u_email2, update_user['email'])
        self.assertEqual('false', str(update_user['enabled']).lower())
        # GET by id after updating
        updated_user = self.client.get_user(user['id'])
        # Assert response body of GET after updating
        self.assertEqual(u_name2, updated_user['name'])
        self.assertEqual(u_email2, updated_user['email'])
        self.assertEqual('false', str(updated_user['enabled']).lower())

    @test.attr(type='smoke')
    @test.idempotent_id('29ed26f4-a74e-4425-9a85-fdb49fa269d2')
    def test_delete_user(self):
        # Delete a user
        test_user = data_utils.rand_name('test_user')
        self.data.setup_test_tenant()
        user = self.client.create_user(test_user, self.alt_password,
                                       self.data.tenant['id'],
                                       self.alt_email)
        self.client.delete_user(user['id'])

    @test.attr(type='smoke')
    @test.idempotent_id('aca696c3-d645-4f45-b728-63646045beb1')
    def test_user_authentication(self):
        # Valid user's token is authenticated
        self.data.setup_test_user()
        # Get a token
        self.token_client.auth(self.data.test_user, self.data.test_password,
                               self.data.test_tenant)
        # Re-auth
        self.token_client.auth(self.data.test_user,
                               self.data.test_password,
                               self.data.test_tenant)

    @test.attr(type='gate')
    @test.idempotent_id('5d1fa498-4c2d-4732-a8fe-2b054598cfdd')
    def test_authentication_request_without_token(self):
        # Request for token authentication with a valid token in header
        self.data.setup_test_user()
        self.token_client.auth(self.data.test_user, self.data.test_password,
                               self.data.test_tenant)
        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)
        # Re-auth
        self.token_client.auth(self.data.test_user,
                               self.data.test_password,
                               self.data.test_tenant)
        self.client.auth_provider.clear_auth()

    @test.attr(type='smoke')
    @test.idempotent_id('a149c02e-e5e0-4b89-809e-7e8faf33ccda')
    def test_get_users(self):
        # Get a list of users and find the test user
        self.data.setup_test_user()
        users = self.client.get_users()
        self.assertThat([u['name'] for u in users],
                        matchers.Contains(self.data.test_user),
                        "Could not find %s" % self.data.test_user)

    @test.attr(type='gate')
    @test.idempotent_id('6e317209-383a-4bed-9f10-075b7c82c79a')
    def test_list_users_for_tenant(self):
        # Return a list of all users for a tenant
        self.data.setup_test_tenant()
        user_ids = list()
        fetched_user_ids = list()
        alt_tenant_user1 = data_utils.rand_name('tenant_user1')
        user1 = self.client.create_user(alt_tenant_user1, 'password1',
                                        self.data.tenant['id'],
                                        'user1@123')
        user_ids.append(user1['id'])
        self.data.users.append(user1)

        alt_tenant_user2 = data_utils.rand_name('tenant_user2')
        user2 = self.client.create_user(alt_tenant_user2, 'password2',
                                        self.data.tenant['id'],
                                        'user2@123')
        user_ids.append(user2['id'])
        self.data.users.append(user2)
        # List of users for the respective tenant ID
        body = self.client.list_users_for_tenant(self.data.tenant['id'])
        for i in body:
            fetched_user_ids.append(i['id'])
        # verifying the user Id in the list
        missing_users =\
            [user for user in user_ids if user not in fetched_user_ids]
        self.assertEqual(0, len(missing_users),
                         "Failed to find user %s in fetched list" %
                         ', '.join(m_user for m_user in missing_users))

    @test.attr(type='gate')
    @test.idempotent_id('a8b54974-40e1-41c0-b812-50fc90827971')
    def test_list_users_with_roles_for_tenant(self):
        # Return list of users on tenant when roles are assigned to users
        self.data.setup_test_user()
        self.data.setup_test_role()
        user = self.get_user_by_name(self.data.test_user)
        tenant = self.get_tenant_by_name(self.data.test_tenant)
        role = self.get_role_by_name(self.data.test_role)
        # Assigning roles to two users
        user_ids = list()
        fetched_user_ids = list()
        user_ids.append(user['id'])
        role = self.client.assign_user_role(tenant['id'], user['id'],
                                            role['id'])

        alt_user2 = data_utils.rand_name('second_user')
        second_user = self.client.create_user(alt_user2, 'password1',
                                              self.data.tenant['id'],
                                              'user2@123')
        user_ids.append(second_user['id'])
        self.data.users.append(second_user)
        role = self.client.assign_user_role(tenant['id'],
                                            second_user['id'],
                                            role['id'])
        # List of users with roles for the respective tenant ID
        body = self.client.list_users_for_tenant(self.data.tenant['id'])
        for i in body:
            fetched_user_ids.append(i['id'])
        # verifying the user Id in the list
        missing_users = [missing_user for missing_user in user_ids
                         if missing_user not in fetched_user_ids]
        self.assertEqual(0, len(missing_users),
                         "Failed to find user %s in fetched list" %
                         ', '.join(m_user for m_user in missing_users))

    @test.attr(type='smoke')
    @test.idempotent_id('1aeb25ac-6ec5-4d8b-97cb-7ac3567a989f')
    def test_update_user_password(self):
        # Test case to check if updating of user password is successful.
        self.data.setup_test_user()
        # Updating the user with new password
        new_pass = data_utils.rand_name('pass')
        update_user = self.client.update_user_password(
            self.data.user['id'], new_pass)
        self.assertEqual(update_user['id'], self.data.user['id'])

        # Validate the updated password
        # Get a token
        body = self.token_client.auth(self.data.test_user, new_pass,
                                      self.data.test_tenant)
        self.assertTrue('id' in body['token'])
