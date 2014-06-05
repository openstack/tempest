from tempest.api.identity import base
from tempest.common.utils import data_utils

class TenantAdmin(base.BaseIdentityAdminTest):
    _interface = 'json'

    def tenant_create_enabled(self):
        # Create a tenant that is enabled
        tenant_name = data_utils.rand_name(name='tenant-')
        resp, body = self.client.create_tenant(tenant_name, enabled=True)
        tenant = body
        tenant_id = body['id']
        st1 = resp['status']
        en1 = body['enabled']
        self.assertTrue(st1.startswith('2'))
        self.assertTrue(en1, 'Enable should be True in response')
        resp, body = self.client.get_tenant(tenant_id)
        en2 = body['enabled']
        self.assertTrue(en2, 'Enable should be True in lookup')
        return tenant