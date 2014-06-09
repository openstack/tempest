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

from six import moves

from tempest.api.identity import base
from tempest.common.utils import data_utils
from tempest import test


class TenantsTestJSON(base.BaseIdentityV2AdminTest):
    _interface = 'json'

    @test.attr(type='gate')
    def test_tenant_list_delete(self):
        # Create several tenants and delete them
        tenants = []
        for _ in moves.xrange(3):
            tenant_name = data_utils.rand_name(name='tenant-new')
            resp, tenant = self.client.create_tenant(tenant_name)
            self.assertEqual(200, resp.status)
            self.data.tenants.append(tenant)
            tenants.append(tenant)
        tenant_ids = map(lambda x: x['id'], tenants)
        resp, body = self.client.list_tenants()
        self.assertEqual(200, resp.status)
        found = [t for t in body if t['id'] in tenant_ids]
        self.assertEqual(len(found), len(tenants), 'Tenants not created')

        for tenant in tenants:
            resp, body = self.client.delete_tenant(tenant['id'])
            self.assertEqual(204, resp.status)
            self.data.tenants.remove(tenant)

        resp, body = self.client.list_tenants()
        found = [tenant for tenant in body if tenant['id'] in tenant_ids]
        self.assertFalse(any(found), 'Tenants failed to delete')

    @test.attr(type='gate')
    def test_tenant_create_with_description(self):
        # Create tenant with a description
        tenant_name = data_utils.rand_name(name='tenant-')
        tenant_desc = data_utils.rand_name(name='desc-')
        resp, body = self.client.create_tenant(tenant_name,
                                               description=tenant_desc)
        tenant = body
        self.data.tenants.append(tenant)
        tenant_id = body['id']
        desc1 = body['description']
        self.assertEqual(200, resp.status)
        self.assertEqual(desc1, tenant_desc, 'Description should have '
                         'been sent in response for create')
        resp, body = self.client.get_tenant(tenant_id)
        desc2 = body['description']
        self.assertEqual(desc2, tenant_desc, 'Description does not appear'
                         'to be set')
        self.client.delete_tenant(tenant_id)
        self.data.tenants.remove(tenant)

    @test.attr(type='gate')
    def test_tenant_create_enabled(self):
        # Create a tenant that is enabled
        tenant_name = data_utils.rand_name(name='tenant-')
        resp, body = self.client.create_tenant(tenant_name, enabled=True)
        tenant = body
        self.data.tenants.append(tenant)
        tenant_id = body['id']
        en1 = body['enabled']
        self.assertEqual(200, resp.status)
        self.assertTrue(en1, 'Enable should be True in response')
        resp, body = self.client.get_tenant(tenant_id)
        en2 = body['enabled']
        self.assertTrue(en2, 'Enable should be True in lookup')
        self.client.delete_tenant(tenant_id)
        self.data.tenants.remove(tenant)

    @test.attr(type='gate')
    def test_tenant_create_not_enabled(self):
        # Create a tenant that is not enabled
        tenant_name = data_utils.rand_name(name='tenant-')
        resp, body = self.client.create_tenant(tenant_name, enabled=False)
        tenant = body
        self.data.tenants.append(tenant)
        tenant_id = body['id']
        en1 = body['enabled']
        self.assertEqual(200, resp.status)
        self.assertEqual('false', str(en1).lower(),
                         'Enable should be False in response')
        resp, body = self.client.get_tenant(tenant_id)
        en2 = body['enabled']
        self.assertEqual('false', str(en2).lower(),
                         'Enable should be False in lookup')
        self.client.delete_tenant(tenant_id)
        self.data.tenants.remove(tenant)

    @test.attr(type='gate')
    def test_tenant_update_name(self):
        # Update name attribute of a tenant
        t_name1 = data_utils.rand_name(name='tenant-')
        resp, body = self.client.create_tenant(t_name1)
        self.assertEqual(200, resp.status)
        tenant = body
        self.data.tenants.append(tenant)

        t_id = body['id']
        resp1_name = body['name']

        t_name2 = data_utils.rand_name(name='tenant2-')
        resp, body = self.client.update_tenant(t_id, name=t_name2)
        resp2_name = body['name']
        self.assertEqual(200, resp.status)
        self.assertNotEqual(resp1_name, resp2_name)

        resp, body = self.client.get_tenant(t_id)
        resp3_name = body['name']

        self.assertNotEqual(resp1_name, resp3_name)
        self.assertEqual(t_name1, resp1_name)
        self.assertEqual(resp2_name, resp3_name)

        self.client.delete_tenant(t_id)
        self.data.tenants.remove(tenant)

    @test.attr(type='gate')
    def test_tenant_update_desc(self):
        # Update description attribute of a tenant
        t_name = data_utils.rand_name(name='tenant-')
        t_desc = data_utils.rand_name(name='desc-')
        resp, body = self.client.create_tenant(t_name, description=t_desc)
        self.assertEqual(200, resp.status)
        tenant = body
        self.data.tenants.append(tenant)

        t_id = body['id']
        resp1_desc = body['description']

        t_desc2 = data_utils.rand_name(name='desc2-')
        resp, body = self.client.update_tenant(t_id, description=t_desc2)
        resp2_desc = body['description']
        self.assertEqual(200, resp.status)
        self.assertNotEqual(resp1_desc, resp2_desc)

        resp, body = self.client.get_tenant(t_id)
        resp3_desc = body['description']

        self.assertNotEqual(resp1_desc, resp3_desc)
        self.assertEqual(t_desc, resp1_desc)
        self.assertEqual(resp2_desc, resp3_desc)

        self.client.delete_tenant(t_id)
        self.data.tenants.remove(tenant)

    @test.attr(type='gate')
    def test_tenant_update_enable(self):
        # Update the enabled attribute of a tenant
        t_name = data_utils.rand_name(name='tenant-')
        t_en = False
        resp, body = self.client.create_tenant(t_name, enabled=t_en)
        self.assertEqual(200, resp.status)
        tenant = body
        self.data.tenants.append(tenant)

        t_id = body['id']
        resp1_en = body['enabled']

        t_en2 = True
        resp, body = self.client.update_tenant(t_id, enabled=t_en2)
        resp2_en = body['enabled']
        self.assertEqual(200, resp.status)
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
