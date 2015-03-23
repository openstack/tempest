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

from tempest_lib.common.utils import data_utils

from tempest.api.identity import base
from tempest import test


class TokensTestJSON(base.BaseIdentityV2AdminTest):

    @test.attr(type='gate')
    @test.idempotent_id('453ad4d5-e486-4b2f-be72-cffc8149e586')
    def test_create_get_delete_token(self):
        # get a token by username and password
        user_name = data_utils.rand_name(name='user')
        user_password = data_utils.rand_name(name='pass')
        # first:create a tenant
        tenant_name = data_utils.rand_name(name='tenant')
        tenant = self.client.create_tenant(tenant_name)
        self.data.tenants.append(tenant)
        # second:create a user
        user = self.client.create_user(user_name, user_password,
                                       tenant['id'], '')
        self.data.users.append(user)
        # then get a token for the user
        body = self.token_client.auth(user_name,
                                      user_password,
                                      tenant['name'])
        self.assertEqual(body['token']['tenant']['name'],
                         tenant['name'])
        # Perform GET Token
        token_id = body['token']['id']
        token_details = self.client.get_token(token_id)
        self.assertEqual(token_id, token_details['token']['id'])
        self.assertEqual(user['id'], token_details['user']['id'])
        self.assertEqual(user_name, token_details['user']['name'])
        self.assertEqual(tenant['name'],
                         token_details['token']['tenant']['name'])
        # then delete the token
        self.client.delete_token(token_id)

    @test.attr(type='gate')
    @test.idempotent_id('25ba82ee-8a32-4ceb-8f50-8b8c71e8765e')
    def test_rescope_token(self):
        """An unscoped token can be requested, that token can be used to
           request a scoped token.
        """

        # Create a user.
        user_name = data_utils.rand_name(name='user')
        user_password = data_utils.rand_name(name='pass')
        tenant_id = None  # No default tenant so will get unscoped token.
        email = ''
        user = self.client.create_user(user_name, user_password,
                                       tenant_id, email)
        self.data.users.append(user)

        # Create a couple tenants.
        tenant1_name = data_utils.rand_name(name='tenant')
        tenant1 = self.client.create_tenant(tenant1_name)
        self.data.tenants.append(tenant1)

        tenant2_name = data_utils.rand_name(name='tenant')
        tenant2 = self.client.create_tenant(tenant2_name)
        self.data.tenants.append(tenant2)

        # Create a role
        role_name = data_utils.rand_name(name='role')
        role = self.client.create_role(role_name)
        self.data.roles.append(role)

        # Grant the user the role on the tenants.
        self.client.assign_user_role(tenant1['id'], user['id'],
                                     role['id'])

        self.client.assign_user_role(tenant2['id'], user['id'],
                                     role['id'])

        # Get an unscoped token.
        body = self.token_client.auth(user_name, user_password)

        token_id = body['token']['id']

        # Use the unscoped token to get a token scoped to tenant1
        body = self.token_client.auth_token(token_id,
                                            tenant=tenant1_name)

        scoped_token_id = body['token']['id']

        # Revoke the scoped token
        self.client.delete_token(scoped_token_id)

        # Use the unscoped token to get a token scoped to tenant2
        body = self.token_client.auth_token(token_id,
                                            tenant=tenant2_name)
