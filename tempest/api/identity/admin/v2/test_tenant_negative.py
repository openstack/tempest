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


class TenantsNegativeTestJSON(base.BaseIdentityV2AdminTest):
    """Negative tests of keystone tenants via v2 API"""

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ca9bb202-63dd-4240-8a07-8ef9c19c04bb')
    def test_list_tenants_by_unauthorized_user(self):
        """Test Non-admin should not be able to list tenants via v2 API"""
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_tenants_client.list_tenants)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('df33926c-1c96-4d8d-a762-79cc6b0c3cf4')
    def test_list_tenant_request_without_token(self):
        """Test listing tenants without a valid token via v2 API

        Listing tenants without a valid token via v2 API should fail.
        """
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized,
                          self.tenants_client.list_tenants)
        self.client.auth_provider.clear_auth()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('162ba316-f18b-4987-8c0c-fd9140cd63ed')
    def test_tenant_delete_by_unauthorized_user(self):
        """Test non-admin should not be able to delete a tenant via v2 API"""
        tenant = self.setup_test_tenant()
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_tenants_client.delete_tenant,
                          tenant['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e450db62-2e9d-418f-893a-54772d6386b1')
    def test_tenant_delete_request_without_token(self):
        """Test deleting a tenant without a valid token via v2 API

        Deleting a tenant without a valid token via v2 API should fail.
        """
        tenant = self.setup_test_tenant()
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized,
                          self.tenants_client.delete_tenant,
                          tenant['id'])
        self.client.auth_provider.clear_auth()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9c9a2aed-6e3c-467a-8f5c-89da9d1b516b')
    def test_delete_non_existent_tenant(self):
        """Test deleting a non existent tenant via v2 API should fail"""
        self.assertRaises(lib_exc.NotFound, self.tenants_client.delete_tenant,
                          data_utils.rand_uuid_hex())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('af16f44b-a849-46cb-9f13-a751c388f739')
    def test_tenant_create_duplicate(self):
        """Test tenant names should be unique via v2 API"""
        tenant_name = data_utils.rand_name(
            name='tenant', prefix=CONF.resource_name_prefix)
        self.setup_test_tenant(name=tenant_name)
        self.assertRaises(lib_exc.Conflict, self.tenants_client.create_tenant,
                          name=tenant_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('d26b278a-6389-4702-8d6e-5980d80137e0')
    def test_create_tenant_by_unauthorized_user(self):
        """Test non-admin user creating a tenant via v2 API

        Non-admin user should not be authorized to create a tenant via v2 API.
        """
        tenant_name = data_utils.rand_name(
            name='tenant', prefix=CONF.resource_name_prefix)
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_tenants_client.create_tenant,
                          name=tenant_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a3ee9d7e-6920-4dd5-9321-d4b2b7f0a638')
    def test_create_tenant_request_without_token(self):
        """Test creating tenant without a token via v2 API is not allowed"""
        tenant_name = data_utils.rand_name(
            name='tenant', prefix=CONF.resource_name_prefix)
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized,
                          self.tenants_client.create_tenant,
                          name=tenant_name)
        self.client.auth_provider.clear_auth()

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('5a2e4ca9-b0c0-486c-9c48-64a94fba2395')
    def test_create_tenant_with_empty_name(self):
        """Test tenant name should not be empty via v2 API"""
        self.assertRaises(lib_exc.BadRequest,
                          self.tenants_client.create_tenant,
                          name='')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('2ff18d1e-dfe3-4359-9dc3-abf582c196b9')
    def test_create_tenants_name_length_over_64(self):
        """Test tenant name length should not exceed 64 via v2 API"""
        tenant_name = 'a' * 65
        self.assertRaises(lib_exc.BadRequest,
                          self.tenants_client.create_tenant,
                          name=tenant_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('bd20dc2a-9557-4db7-b755-f48d952ad706')
    def test_update_non_existent_tenant(self):
        """Test updating a non existent tenant via v2 API should fail"""
        self.assertRaises(lib_exc.NotFound, self.tenants_client.update_tenant,
                          data_utils.rand_uuid_hex())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('41704dc5-c5f7-4f79-abfa-76e6fedc570b')
    def test_tenant_update_by_unauthorized_user(self):
        """Test non-admin user updating a tenant via v2 API

        Non-admin user should not be able to update a tenant via v2 API
        """
        tenant = self.setup_test_tenant()
        self.assertRaises(lib_exc.Forbidden,
                          self.non_admin_tenants_client.update_tenant,
                          tenant['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7a421573-72c7-4c22-a98e-ce539219c657')
    def test_tenant_update_request_without_token(self):
        """Test updating a tenant without a valid token via v2 API

        Updating a tenant without a valid token via v2 API should fail
        """
        tenant = self.setup_test_tenant()
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(lib_exc.Unauthorized,
                          self.tenants_client.update_tenant,
                          tenant['id'])
        self.client.auth_provider.clear_auth()
