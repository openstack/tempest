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

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class TenantsNegativeTestJSON(base.BaseIdentityV2AdminTest):
    _interface = 'json'

    @test.attr(type=['negative', 'gate'])
    def test_list_tenants_by_unauthorized_user(self):
        # Non-administrator user should not be able to list tenants
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.list_tenants)

    @test.attr(type=['negative', 'gate'])
    def test_list_tenant_request_without_token(self):
        # Request to list tenants without a valid token should fail
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.list_tenants)
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    def test_tenant_delete_by_unauthorized_user(self):
        # Non-administrator user should not be able to delete a tenant
        tenant_name = data_utils.rand_name(name='tenant-')
        _, tenant = self.client.create_tenant(tenant_name)
        self.data.tenants.append(tenant)
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.delete_tenant, tenant['id'])

    @test.attr(type=['negative', 'gate'])
    def test_tenant_delete_request_without_token(self):
        # Request to delete a tenant without a valid token should fail
        tenant_name = data_utils.rand_name(name='tenant-')
        _, tenant = self.client.create_tenant(tenant_name)
        self.data.tenants.append(tenant)
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.delete_tenant,
                          tenant['id'])
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    def test_delete_non_existent_tenant(self):
        # Attempt to delete a non existent tenant should fail
        self.assertRaises(exceptions.NotFound, self.client.delete_tenant,
                          str(uuid.uuid4().hex))

    @test.attr(type=['negative', 'gate'])
    def test_tenant_create_duplicate(self):
        # Tenant names should be unique
        tenant_name = data_utils.rand_name(name='tenant-')
        _, body = self.client.create_tenant(tenant_name)
        tenant = body
        self.data.tenants.append(tenant)
        tenant1_id = body.get('id')

        self.addCleanup(self.client.delete_tenant, tenant1_id)
        self.addCleanup(self.data.tenants.remove, tenant)
        self.assertRaises(exceptions.Conflict, self.client.create_tenant,
                          tenant_name)

    @test.attr(type=['negative', 'gate'])
    def test_create_tenant_by_unauthorized_user(self):
        # Non-administrator user should not be authorized to create a tenant
        tenant_name = data_utils.rand_name(name='tenant-')
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.create_tenant, tenant_name)

    @test.attr(type=['negative', 'gate'])
    def test_create_tenant_request_without_token(self):
        # Create tenant request without a token should not be authorized
        tenant_name = data_utils.rand_name(name='tenant-')
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.create_tenant,
                          tenant_name)
        self.client.auth_provider.clear_auth()

    @test.attr(type=['negative', 'gate'])
    def test_create_tenant_with_empty_name(self):
        # Tenant name should not be empty
        self.assertRaises(exceptions.BadRequest, self.client.create_tenant,
                          name='')

    @test.attr(type=['negative', 'gate'])
    def test_create_tenants_name_length_over_64(self):
        # Tenant name length should not be greater than 64 characters
        tenant_name = 'a' * 65
        self.assertRaises(exceptions.BadRequest, self.client.create_tenant,
                          tenant_name)

    @test.attr(type=['negative', 'gate'])
    def test_update_non_existent_tenant(self):
        # Attempt to update a non existent tenant should fail
        self.assertRaises(exceptions.NotFound, self.client.update_tenant,
                          str(uuid.uuid4().hex))

    @test.attr(type=['negative', 'gate'])
    def test_tenant_update_by_unauthorized_user(self):
        # Non-administrator user should not be able to update a tenant
        tenant_name = data_utils.rand_name(name='tenant-')
        _, tenant = self.client.create_tenant(tenant_name)
        self.data.tenants.append(tenant)
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.update_tenant, tenant['id'])

    @test.attr(type=['negative', 'gate'])
    def test_tenant_update_request_without_token(self):
        # Request to update a tenant without a valid token should fail
        tenant_name = data_utils.rand_name(name='tenant-')
        _, tenant = self.client.create_tenant(tenant_name)
        self.data.tenants.append(tenant)
        token = self.client.auth_provider.get_token()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.update_tenant,
                          tenant['id'])
        self.client.auth_provider.clear_auth()


class TenantsNegativeTestXML(TenantsNegativeTestJSON):
    _interface = 'xml'
