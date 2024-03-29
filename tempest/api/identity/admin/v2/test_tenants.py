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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class TenantsTestJSON(base.BaseIdentityV2AdminTest):
    """Test identity tenants via v2 API"""

    @decorators.idempotent_id('16c6e05c-6112-4b0e-b83f-5e43f221b6b0')
    def test_tenant_list_delete(self):
        """Test listing and deleting tenants via v2 API

        Create several tenants and delete them
        """
        tenants = []
        for _ in range(3):
            tenant = self.setup_test_tenant()
            tenants.append(tenant)
        tenant_ids = [tn['id'] for tn in tenants]
        body = self.tenants_client.list_tenants()['tenants']
        found = [t for t in body if t['id'] in tenant_ids]
        self.assertEqual(len(found), len(tenants), 'Tenants not created')

        for tenant in tenants:
            self.tenants_client.delete_tenant(tenant['id'])

        body = self.tenants_client.list_tenants()['tenants']
        found = [tenant for tenant in body if tenant['id'] in tenant_ids]
        self.assertEmpty(found, 'Tenants failed to delete')

    @decorators.idempotent_id('d25e9f24-1310-4d29-b61b-d91299c21d6d')
    def test_tenant_create_with_description(self):
        """Test creating tenant with a description via v2 API"""
        tenant_desc = data_utils.rand_name(
            name='desc', prefix=CONF.resource_name_prefix)
        tenant = self.setup_test_tenant(description=tenant_desc)
        tenant_id = tenant['id']
        desc1 = tenant['description']
        self.assertEqual(desc1, tenant_desc, 'Description should have '
                         'been sent in response for create')
        body = self.tenants_client.show_tenant(tenant_id)['tenant']
        desc2 = body['description']
        self.assertEqual(desc2, tenant_desc, 'Description does not appear '
                         'to be set')
        self.tenants_client.delete_tenant(tenant_id)

    @decorators.idempotent_id('670bdddc-1cd7-41c7-b8e2-751cfb67df50')
    def test_tenant_create_enabled(self):
        """Test creating a tenant that is enabled via v2 API"""
        tenant = self.setup_test_tenant(enabled=True)
        tenant_id = tenant['id']
        self.assertTrue(tenant['enabled'], 'Enable should be True in response')
        body = self.tenants_client.show_tenant(tenant_id)['tenant']
        self.assertTrue(body['enabled'], 'Enable should be True in lookup')
        self.tenants_client.delete_tenant(tenant_id)

    @decorators.idempotent_id('3be22093-b30f-499d-b772-38340e5e16fb')
    def test_tenant_create_not_enabled(self):
        """Test creating a tenant that is not enabled via v2 API"""
        tenant = self.setup_test_tenant(enabled=False)
        tenant_id = tenant['id']
        self.assertFalse(tenant['enabled'],
                         'Enable should be False in response')
        body = self.tenants_client.show_tenant(tenant_id)['tenant']
        self.assertFalse(body['enabled'],
                         'Enable should be False in lookup')
        self.tenants_client.delete_tenant(tenant_id)

    @decorators.idempotent_id('781f2266-d128-47f3-8bdb-f70970add238')
    def test_tenant_update_name(self):
        """Test updating name attribute of a tenant via v2 API"""
        t_name1 = data_utils.rand_name(
            name='tenant', prefix=CONF.resource_name_prefix)
        tenant = self.setup_test_tenant(name=t_name1)
        t_id = tenant['id']
        resp1_name = tenant['name']

        t_name2 = data_utils.rand_name(
            name='tenant2', prefix=CONF.resource_name_prefix)
        body = self.tenants_client.update_tenant(t_id, name=t_name2)['tenant']
        resp2_name = body['name']
        self.assertNotEqual(resp1_name, resp2_name)

        body = self.tenants_client.show_tenant(t_id)['tenant']
        resp3_name = body['name']

        self.assertNotEqual(resp1_name, resp3_name)
        self.assertEqual(t_name1, resp1_name)
        self.assertEqual(resp2_name, resp3_name)

        self.tenants_client.delete_tenant(t_id)

    @decorators.idempotent_id('859fcfe1-3a03-41ef-86f9-b19a47d1cd87')
    def test_tenant_update_desc(self):
        """Test updating description attribute of a tenant via v2 API"""
        t_desc = data_utils.rand_name(
            name='desc', prefix=CONF.resource_name_prefix)
        tenant = self.setup_test_tenant(description=t_desc)
        t_id = tenant['id']
        resp1_desc = tenant['description']

        t_desc2 = data_utils.rand_name(
            name='desc2', prefix=CONF.resource_name_prefix)
        body = self.tenants_client.update_tenant(t_id, description=t_desc2)
        updated_tenant = body['tenant']
        resp2_desc = updated_tenant['description']
        self.assertNotEqual(resp1_desc, resp2_desc)

        body = self.tenants_client.show_tenant(t_id)['tenant']
        resp3_desc = body['description']

        self.assertNotEqual(resp1_desc, resp3_desc)
        self.assertEqual(t_desc, resp1_desc)
        self.assertEqual(resp2_desc, resp3_desc)

        self.tenants_client.delete_tenant(t_id)

    @decorators.idempotent_id('8fc8981f-f12d-4c66-9972-2bdcf2bc2e1a')
    def test_tenant_update_enable(self):
        """Test updating the enabled attribute of a tenant via v2 API"""
        t_en = False
        tenant = self.setup_test_tenant(enabled=t_en)
        t_id = tenant['id']
        resp1_en = tenant['enabled']

        t_en2 = True
        body = self.tenants_client.update_tenant(t_id, enabled=t_en2)
        updated_tenant = body['tenant']
        resp2_en = updated_tenant['enabled']
        self.assertNotEqual(resp1_en, resp2_en)

        body = self.tenants_client.show_tenant(t_id)['tenant']
        resp3_en = body['enabled']

        self.assertNotEqual(resp1_en, resp3_en)
        self.assertFalse(tenant['enabled'])
        self.assertEqual(resp2_en, resp3_en)

        self.tenants_client.delete_tenant(t_id)
