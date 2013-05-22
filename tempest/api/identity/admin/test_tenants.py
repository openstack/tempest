# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class TenantsTestJSON(base.BaseIdentityAdminTest):
    _interface = 'json'

    @attr(type='gate')
    def test_list_tenants_by_unauthorized_user(self):
        # Non-admin user should not be able to list tenants
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.list_tenants)

    @attr(type='gate')
    def test_list_tenant_request_without_token(self):
        # Request to list tenants without a valid token should fail
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.list_tenants)
        self.client.clear_auth()

    @attr(type='gate')
    def test_tenant_list_delete(self):
        # Create several tenants and delete them
        tenants = []
        for _ in xrange(3):
            resp, tenant = self.client.create_tenant(rand_name('tenant-new'))
            self.data.tenants.append(tenant)
            tenants.append(tenant)
        tenant_ids = map(lambda x: x['id'], tenants)
        resp, body = self.client.list_tenants()
        self.assertTrue(resp['status'].startswith('2'))
        found = [tenant for tenant in body if tenant['id'] in tenant_ids]
        self.assertEqual(len(found), len(tenants), 'Tenants not created')

        for tenant in tenants:
            resp, body = self.client.delete_tenant(tenant['id'])
            self.assertTrue(resp['status'].startswith('2'))
            self.data.tenants.remove(tenant)

        resp, body = self.client.list_tenants()
        found = [tenant for tenant in body if tenant['id'] in tenant_ids]
        self.assertFalse(any(found), 'Tenants failed to delete')

    @attr(type='gate')
    def test_tenant_delete_by_unauthorized_user(self):
        # Non-admin user should not be able to delete a tenant
        tenant_name = rand_name('tenant-')
        resp, tenant = self.client.create_tenant(tenant_name)
        self.data.tenants.append(tenant)
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.delete_tenant, tenant['id'])

    @attr(type='gate')
    def test_tenant_delete_request_without_token(self):
        # Request to delete a tenant without a valid token should fail
        tenant_name = rand_name('tenant-')
        resp, tenant = self.client.create_tenant(tenant_name)
        self.data.tenants.append(tenant)
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.delete_tenant,
                          tenant['id'])
        self.client.clear_auth()

    @attr(type='gate')
    def test_delete_non_existent_tenant(self):
        # Attempt to delete a non existent tenant should fail
        self.assertRaises(exceptions.NotFound, self.client.delete_tenant,
                          'junk_tenant_123456abc')

    @attr(type='gate')
    def test_tenant_create_with_description(self):
        # Create tenant with a description
        tenant_name = rand_name('tenant-')
        tenant_desc = rand_name('desc-')
        resp, body = self.client.create_tenant(tenant_name,
                                               description=tenant_desc)
        tenant = body
        self.data.tenants.append(tenant)
        st1 = resp['status']
        tenant_id = body['id']
        desc1 = body['description']
        self.assertTrue(st1.startswith('2'))
        self.assertEqual(desc1, tenant_desc, 'Description should have '
                         'been sent in response for create')
        resp, body = self.client.get_tenant(tenant_id)
        desc2 = body['description']
        self.assertEqual(desc2, tenant_desc, 'Description does not appear'
                         'to be set')
        self.client.delete_tenant(tenant_id)
        self.data.tenants.remove(tenant)

    @attr(type='gate')
    def test_tenant_create_enabled(self):
        # Create a tenant that is enabled
        tenant_name = rand_name('tenant-')
        resp, body = self.client.create_tenant(tenant_name, enabled=True)
        tenant = body
        self.data.tenants.append(tenant)
        tenant_id = body['id']
        st1 = resp['status']
        en1 = body['enabled']
        self.assertTrue(st1.startswith('2'))
        self.assertTrue(en1, 'Enable should be True in response')
        resp, body = self.client.get_tenant(tenant_id)
        en2 = body['enabled']
        self.assertTrue(en2, 'Enable should be True in lookup')
        self.client.delete_tenant(tenant_id)
        self.data.tenants.remove(tenant)

    @attr(type='gate')
    def test_tenant_create_not_enabled(self):
        # Create a tenant that is not enabled
        tenant_name = rand_name('tenant-')
        resp, body = self.client.create_tenant(tenant_name, enabled=False)
        tenant = body
        self.data.tenants.append(tenant)
        tenant_id = body['id']
        st1 = resp['status']
        en1 = body['enabled']
        self.assertTrue(st1.startswith('2'))
        self.assertEqual('false', str(en1).lower(),
                         'Enable should be False in response')
        resp, body = self.client.get_tenant(tenant_id)
        en2 = body['enabled']
        self.assertEqual('false', str(en2).lower(),
                         'Enable should be False in lookup')
        self.client.delete_tenant(tenant_id)
        self.data.tenants.remove(tenant)

    @attr(type='gate')
    def test_tenant_create_duplicate(self):
        # Tenant names should be unique
        tenant_name = rand_name('tenant-dup-')
        resp, body = self.client.create_tenant(tenant_name)
        tenant = body
        self.data.tenants.append(tenant)
        tenant1_id = body.get('id')

        self.addCleanup(self.client.delete_tenant, tenant1_id)
        self.addCleanup(self.data.tenants.remove, tenant)
        self.assertRaises(exceptions.Duplicate, self.client.create_tenant,
                          tenant_name)

    @attr(type='gate')
    def test_create_tenant_by_unauthorized_user(self):
        # Non-admin user should not be authorized to create a tenant
        tenant_name = rand_name('tenant-')
        self.assertRaises(exceptions.Unauthorized,
                          self.non_admin_client.create_tenant, tenant_name)

    @attr(type='gate')
    def test_create_tenant_request_without_token(self):
        # Create tenant request without a token should not be authorized
        tenant_name = rand_name('tenant-')
        token = self.client.get_auth()
        self.client.delete_token(token)
        self.assertRaises(exceptions.Unauthorized, self.client.create_tenant,
                          tenant_name)
        self.client.clear_auth()

    @attr(type='gate')
    def test_create_tenant_with_empty_name(self):
        # Tenant name should not be empty
        self.assertRaises(exceptions.BadRequest, self.client.create_tenant,
                          name='')

    @attr(type='gate')
    def test_create_tenants_name_length_over_64(self):
        # Tenant name length should not be greater than 64 characters
        tenant_name = 'a' * 65
        self.assertRaises(exceptions.BadRequest, self.client.create_tenant,
                          tenant_name)

    @attr(type='gate')
    def test_tenant_update_name(self):
        # Update name attribute of a tenant
        t_name1 = rand_name('tenant-')
        resp, body = self.client.create_tenant(t_name1)
        tenant = body
        self.data.tenants.append(tenant)

        t_id = body['id']
        resp1_name = body['name']

        t_name2 = rand_name('tenant2-')
        resp, body = self.client.update_tenant(t_id, name=t_name2)
        st2 = resp['status']
        resp2_name = body['name']
        self.assertTrue(st2.startswith('2'))
        self.assertNotEqual(resp1_name, resp2_name)

        resp, body = self.client.get_tenant(t_id)
        resp3_name = body['name']

        self.assertNotEqual(resp1_name, resp3_name)
        self.assertEqual(t_name1, resp1_name)
        self.assertEqual(resp2_name, resp3_name)

        self.client.delete_tenant(t_id)
        self.data.tenants.remove(tenant)

    @attr(type='gate')
    def test_tenant_update_desc(self):
        # Update description attribute of a tenant
        t_name = rand_name('tenant-')
        t_desc = rand_name('desc-')
        resp, body = self.client.create_tenant(t_name, description=t_desc)
        tenant = body
        self.data.tenants.append(tenant)

        t_id = body['id']
        resp1_desc = body['description']

        t_desc2 = rand_name('desc2-')
        resp, body = self.client.update_tenant(t_id, description=t_desc2)
        st2 = resp['status']
        resp2_desc = body['description']
        self.assertTrue(st2.startswith('2'))
        self.assertNotEqual(resp1_desc, resp2_desc)

        resp, body = self.client.get_tenant(t_id)
        resp3_desc = body['description']

        self.assertNotEqual(resp1_desc, resp3_desc)
        self.assertEqual(t_desc, resp1_desc)
        self.assertEqual(resp2_desc, resp3_desc)

        self.client.delete_tenant(t_id)
        self.data.tenants.remove(tenant)

    @attr(type='gate')
    def test_tenant_update_enable(self):
        # Update the enabled attribute of a tenant
        t_name = rand_name('tenant-')
        t_en = False
        resp, body = self.client.create_tenant(t_name, enabled=t_en)
        tenant = body
        self.data.tenants.append(tenant)

        t_id = body['id']
        resp1_en = body['enabled']

        t_en2 = True
        resp, body = self.client.update_tenant(t_id, enabled=t_en2)
        st2 = resp['status']
        resp2_en = body['enabled']
        self.assertTrue(st2.startswith('2'))
        self.assertNotEqual(resp1_en, resp2_en)

        resp, body = self.client.get_tenant(t_id)
        resp3_en = body['enabled']

        self.assertNotEqual(resp1_en, resp3_en)
        self.assertEqual('false', str(resp1_en).lower())
        self.assertEqual(resp2_en, resp3_en)

        self.client.delete_tenant(t_id)
        self.data.tenants.remove(tenant)


class TenantsTestXML(TenantsTestJSON):
    _interface = 'xml'
