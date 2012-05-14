import nose
from tempest import exceptions
from tempest.common.utils.data_utils import rand_name
from base_admin_test import BaseAdminTest


class TenantsTest(BaseAdminTest):

    @classmethod
    def setUpClass(cls):
        super(TenantsTest, cls).setUpClass()

        if not cls.client.has_admin_extensions():
            raise nose.SkipTest("Admin extensions disabled")

        for _ in xrange(5):
            resp, tenant = cls.client.create_tenant(rand_name('tenant-'))
            cls.data.tenants.append(tenant)

    @classmethod
    def tearDownClass(cls):
        super(TenantsTest, cls).tearDownClass()

    def test_list_tenants(self):
        """Return a list of all tenants"""
        resp, body = self.client.list_tenants()
        found = [tenant for tenant in body if tenant in self.data.tenants]
        self.assertTrue(any(found), 'List did not return newly created '
                        'tenants')
        self.assertEqual(len(found), len(self.data.tenants))
        self.assertTrue(resp['status'].startswith('2'))

    def test_tenant_delete(self):
        """Create several tenants and delete them"""
        tenants = []
        for _ in xrange(5):
            resp, body = self.client.create_tenant(rand_name('tenant-new'))
            tenants.append(body['id'])

        resp, body = self.client.list_tenants()
        found_1 = [tenant for tenant in body if tenant['id'] in tenants]
        for tenant_id in tenants:
            resp, body = self.client.delete_tenant(tenant_id)
            self.assertTrue(resp['status'].startswith('2'))

        resp, body = self.client.list_tenants()
        found_2 = [tenant for tenant in body if tenant['id'] in tenants]
        self.assertTrue(any(found_1), 'Tenants not created')
        self.assertFalse(any(found_2), 'Tenants failed to delete')

    def test_tenant_create_with_description(self):
        """Create tenant with a description"""
        tenant_name = rand_name('tenant-')
        tenant_desc = rand_name('desc-')
        resp, body = self.client.create_tenant(tenant_name,
                                               description=tenant_desc)
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

    def test_tenant_create_enabled(self):
        """Create a tenant that is enabled"""
        tenant_name = rand_name('tenant-')
        resp, body = self.client.create_tenant(tenant_name, enabled=True)
        tenant_id = body['id']
        st1 = resp['status']
        en1 = body['enabled']
        self.assertTrue(st1.startswith('2'))
        self.assertTrue(en1, 'Enable should be True in response')
        resp, body = self.client.get_tenant(tenant_id)
        en2 = body['enabled']
        self.assertTrue(en2, 'Enable should be True in lookup')
        self.client.delete_tenant(tenant_id)

    def test_tenant_create_not_enabled(self):
        """Create a tenant that is not enabled"""
        tenant_name = rand_name('tenant-')
        resp, body = self.client.create_tenant(tenant_name, enabled=False)
        tenant_id = body['id']
        st1 = resp['status']
        en1 = body['enabled']
        self.assertTrue(st1.startswith('2'))
        self.assertFalse(en1, 'Enable should be False in response')
        resp, body = self.client.get_tenant(tenant_id)
        en2 = body['enabled']
        self.assertFalse(en2, 'Enable should be False in lookup')
        self.client.delete_tenant(tenant_id)

    def test_tenant_create_duplicate(self):
        """Tenant names should be unique"""
        tenant_name = rand_name('tenant-dup-')
        resp, body = self.client.create_tenant(tenant_name)
        tenant1_id = body.get('id')

        try:
            resp, body = self.client.create_tenant(tenant_name)
            # this should have raised an exception
            self.fail('Should not be able to create a duplicate tenant name')
        except exceptions.Duplicate:
            pass
        if tenant1_id:
            self.client.delete_tenant(tenant1_id)

    def test_tenant_update_name(self):
        """Update name attribute of a tenant"""
        t_name1 = rand_name('tenant-')
        resp, body = self.client.create_tenant(t_name1)
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

    def test_tenant_update_desc(self):
        """Update description attribute of a tenant"""
        t_name = rand_name('tenant-')
        t_desc = rand_name('desc-')
        resp, body = self.client.create_tenant(t_name, description=t_desc)
        t_id = body['id']
        resp1_desc = body['description']

        t_desc2 = rand_name('desc2-')
        resp, body = self.client.update_tenant(t_id, description=t_desc2)
        st2 = resp['status']
        resp2_desc = body['extra']['description']
        self.assertTrue(st2.startswith('2'))
        self.assertNotEqual(resp1_desc, resp2_desc)

        resp, body = self.client.get_tenant(t_id)
        resp3_desc = body['description']

        self.assertNotEqual(resp1_desc, resp3_desc)
        self.assertEqual(t_desc, resp1_desc)
        self.assertEqual(resp2_desc, resp3_desc)

        self.client.delete_tenant(t_id)

    def test_tenant_update_enable(self):
        """Update the enabled attribute of a tenant"""
        t_name = rand_name('tenant-')
        t_en = False
        resp, body = self.client.create_tenant(t_name, enabled=t_en)
        t_id = body['id']
        resp1_en = body['enabled']

        t_en2 = True
        resp, body = self.client.update_tenant(t_id, enabled=t_en2)
        st2 = resp['status']
        resp2_en = body['extra']['enabled']
        self.assertTrue(st2.startswith('2'))
        self.assertNotEqual(resp1_en, resp2_en)

        resp, body = self.client.get_tenant(t_id)
        resp3_en = body['enabled']

        self.assertNotEqual(resp1_en, resp3_en)
        self.assertEqual(t_en, resp1_en)
        self.assertEqual(resp2_en, resp3_en)

        self.client.delete_tenant(t_id)
