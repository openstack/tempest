
from tempest.common.utils.data_utils import rand_name
from tempest import clients


class TenantAdmin(object):
    _interface = 'json'

    def __init__(self):
            os = clients.AdminManager(interface=self._interface)
            self.client = os.identity_client
            self.tenants = []


    def tenant_create_enabled(self):
        # Create a tenant that is enabled
        tenant_name = rand_name(name='tenant-')
        description = rand_name('desc_')
        #resp, tenant = self.client.create_tenant(tenant_name, enabled=True)
        resp, tenant = self.client.create_tenant(
            name= tenant_name,
            description= description)
        self.tenants.append(tenant)
        return tenant

    def teardown_all(self):
            for tenant in self.tenants:
                self.client.delete_tenant(tenant['id'])