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


class TokensTestJSON(base.BaseIdentityV2AdminTest):

    @decorators.idempotent_id('453ad4d5-e486-4b2f-be72-cffc8149e586')
    def test_create_check_get_delete_token(self):
        # get a token by username and password
        user_name = data_utils.rand_name(name='user')
        user_password = data_utils.rand_password()
        # first:create a tenant
        tenant = self.setup_test_tenant()
        # second:create a user
        user = self.create_test_user(name=user_name,
                                     password=user_password,
                                     tenantId=tenant['id'],
                                     email='')
        # then get a token for the user
        body = self.token_client.auth(user_name,
                                      user_password,
                                      tenant['name'])
        self.assertEqual(body['token']['tenant']['name'],
                         tenant['name'])
        # Perform GET Token
        token_id = body['token']['id']
        self.client.check_token_existence(token_id)
        token_details = self.client.show_token(token_id)['access']
        self.assertEqual(token_id, token_details['token']['id'])
        self.assertEqual(user['id'], token_details['user']['id'])
        self.assertEqual(user_name, token_details['user']['name'])
        self.assertEqual(tenant['name'],
                         token_details['token']['tenant']['name'])
        # then delete the token
        self.client.delete_token(token_id)
        self.assertRaises(lib_exc.NotFound,
                          self.client.check_token_existence,
                          token_id)

    @decorators.idempotent_id('25ba82ee-8a32-4ceb-8f50-8b8c71e8765e')
    def test_rescope_token(self):
        """An unscoped token can be requested

        That token can be used to request a scoped token.
        """

        # Create a user.
        user_name = data_utils.rand_name(name='user')
        user_password = data_utils.rand_password()
        tenant_id = None  # No default tenant so will get unscoped token.
        user = self.create_test_user(name=user_name,
                                     password=user_password,
                                     tenantId=tenant_id,
                                     email='')

        # Create a couple tenants.
        tenant1_name = data_utils.rand_name(name='tenant')
        tenant1 = self.setup_test_tenant(name=tenant1_name)

        tenant2_name = data_utils.rand_name(name='tenant')
        tenant2 = self.setup_test_tenant(name=tenant2_name)

        # Create a role
        role = self.setup_test_role()

        # Grant the user the role on the tenants.
        self.roles_client.create_user_role_on_project(tenant1['id'],
                                                      user['id'],
                                                      role['id'])

        self.roles_client.create_user_role_on_project(tenant2['id'],
                                                      user['id'],
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

    @decorators.idempotent_id('ca3ea6f7-ed08-4a61-adbd-96906456ad31')
    def test_list_endpoints_for_token(self):
        tempest_services = ['keystone', 'nova', 'neutron', 'swift', 'cinder',
                            'neutron']
        # get a token for the user
        creds = self.os_primary.credentials
        username = creds.username
        password = creds.password
        tenant_name = creds.tenant_name
        token = self.token_client.auth(username,
                                       password,
                                       tenant_name)['token']
        endpoints = self.client.list_endpoints_for_token(
            token['id'])['endpoints']
        self.assertIsInstance(endpoints, list)
        # Store list of service names
        service_names = [e['name'] for e in endpoints]
        # Get the list of available services. Keystone is always available.
        available_services = [s[0] for s in list(
            CONF.service_available.items()) if s[1] is True] + ['keystone']
        # Verify that all available services are present.
        for service in tempest_services:
            if service in available_services:
                self.assertIn(service, service_names)
