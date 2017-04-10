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

import time

from testtools import matchers

from tempest.api.identity import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class UsersTestJSON(base.BaseIdentityV2AdminTest):

    @classmethod
    def resource_setup(cls):
        super(UsersTestJSON, cls).resource_setup()
        cls.alt_user = data_utils.rand_name('test_user')
        cls.alt_email = cls.alt_user + '@testmail.tm'

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('2d55a71e-da1d-4b43-9c03-d269fd93d905')
    def test_create_user(self):
        # Create a user
        tenant = self.setup_test_tenant()
        user = self.create_test_user(name=self.alt_user, tenantId=tenant['id'])
        self.assertEqual(self.alt_user, user['name'])

    @decorators.idempotent_id('89d9fdb8-15c2-4304-a429-48715d0af33d')
    def test_create_user_with_enabled(self):
        # Create a user with enabled : False
        tenant = self.setup_test_tenant()
        name = data_utils.rand_name('test_user')
        user = self.create_test_user(name=name,
                                     tenantId=tenant['id'],
                                     email=self.alt_email,
                                     enabled=False)
        self.assertEqual(name, user['name'])
        self.assertEqual(False, user['enabled'])
        self.assertEqual(self.alt_email, user['email'])

    @decorators.idempotent_id('39d05857-e8a5-4ed4-ba83-0b52d3ab97ee')
    def test_update_user(self):
        # Test case to check if updating of user attributes is successful.
        tenant = self.setup_test_tenant()
        user = self.create_test_user(tenantId=tenant['id'])

        # Updating user details with new values
        u_name2 = data_utils.rand_name('user2')
        u_email2 = u_name2 + '@testmail.tm'
        update_user = self.users_client.update_user(user['id'], name=u_name2,
                                                    email=u_email2,
                                                    enabled=False)['user']
        self.assertEqual(u_name2, update_user['name'])
        self.assertEqual(u_email2, update_user['email'])
        self.assertEqual(False, update_user['enabled'])
        # GET by id after updating
        updated_user = self.users_client.show_user(user['id'])['user']
        # Assert response body of GET after updating
        self.assertEqual(u_name2, updated_user['name'])
        self.assertEqual(u_email2, updated_user['email'])
        self.assertEqual(False, update_user['enabled'])

    @decorators.idempotent_id('29ed26f4-a74e-4425-9a85-fdb49fa269d2')
    def test_delete_user(self):
        # Delete a user
        tenant = self.setup_test_tenant()
        user = self.create_test_user(tenantId=tenant['id'])
        self.users_client.delete_user(user['id'])

    @decorators.idempotent_id('aca696c3-d645-4f45-b728-63646045beb1')
    def test_user_authentication(self):
        # Valid user's token is authenticated
        password = data_utils.rand_password()
        user = self.setup_test_user(password)
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        # Get a token
        self.token_client.auth(user['name'],
                               password,
                               tenant['name'])
        # Re-auth
        self.token_client.auth(user['name'],
                               password,
                               tenant['name'])

    @decorators.idempotent_id('5d1fa498-4c2d-4732-a8fe-2b054598cfdd')
    def test_authentication_request_without_token(self):
        # Request for token authentication with a valid token in header
        password = data_utils.rand_password()
        user = self.setup_test_user(password)
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        self.token_client.auth(user['name'],
                               password,
                               tenant['name'])
        # Get the token of the current client
        token = self.client.auth_provider.get_token()
        # Delete the token from database
        self.client.delete_token(token)
        # Re-auth
        self.token_client.auth(user['name'],
                               password,
                               tenant['name'])
        self.client.auth_provider.clear_auth()

    @decorators.idempotent_id('a149c02e-e5e0-4b89-809e-7e8faf33ccda')
    def test_get_users(self):
        # Get a list of users and find the test user
        user = self.setup_test_user()
        users = self.users_client.list_users()['users']
        self.assertThat([u['name'] for u in users],
                        matchers.Contains(user['name']),
                        "Could not find %s" % user['name'])

    @decorators.idempotent_id('6e317209-383a-4bed-9f10-075b7c82c79a')
    def test_list_users_for_tenant(self):
        # Return a list of all users for a tenant
        tenant = self.setup_test_tenant()
        user_ids = list()
        fetched_user_ids = list()
        user1 = self.create_test_user(tenantId=tenant['id'])
        user_ids.append(user1['id'])
        user2 = self.create_test_user(tenantId=tenant['id'])
        user_ids.append(user2['id'])
        # List of users for the respective tenant ID
        body = (self.tenants_client.list_tenant_users(tenant['id'])
                ['users'])
        for i in body:
            fetched_user_ids.append(i['id'])
        # verifying the user Id in the list
        missing_users =\
            [user for user in user_ids if user not in fetched_user_ids]
        self.assertEmpty(missing_users,
                         "Failed to find user %s in fetched list" %
                         ', '.join(m_user for m_user in missing_users))

    @decorators.idempotent_id('a8b54974-40e1-41c0-b812-50fc90827971')
    def test_list_users_with_roles_for_tenant(self):
        # Return list of users on tenant when roles are assigned to users
        user = self.setup_test_user()
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        role = self.setup_test_role()
        # Assigning roles to two users
        user_ids = list()
        fetched_user_ids = list()
        user_ids.append(user['id'])
        role = self.roles_client.create_user_role_on_project(
            tenant['id'], user['id'], role['id'])['role']

        second_user = self.create_test_user(tenantId=tenant['id'])
        user_ids.append(second_user['id'])
        role = self.roles_client.create_user_role_on_project(
            tenant['id'], second_user['id'], role['id'])['role']
        # List of users with roles for the respective tenant ID
        body = (self.tenants_client.list_tenant_users(tenant['id'])['users'])
        for i in body:
            fetched_user_ids.append(i['id'])
        # verifying the user Id in the list
        missing_users = [missing_user for missing_user in user_ids
                         if missing_user not in fetched_user_ids]
        self.assertEmpty(missing_users,
                         "Failed to find user %s in fetched list" %
                         ', '.join(m_user for m_user in missing_users))

    @decorators.idempotent_id('1aeb25ac-6ec5-4d8b-97cb-7ac3567a989f')
    def test_update_user_password(self):
        # Test case to check if updating of user password is successful.
        user = self.setup_test_user()
        tenant = self.tenants_client.show_tenant(user['tenantId'])['tenant']
        # Updating the user with new password
        new_pass = data_utils.rand_password()
        update_user = self.users_client.update_user_password(
            user['id'], password=new_pass)['user']
        self.assertEqual(update_user['id'], user['id'])
        # NOTE(morganfainberg): Fernet tokens are not subsecond aware and
        # Keystone should only be precise to the second. Sleep to ensure
        # we are passing the second boundary.
        time.sleep(1)
        # Validate the updated password through getting a token.
        body = self.token_client.auth(user['name'], new_pass,
                                      tenant['name'])
        self.assertIn('id', body['token'])
