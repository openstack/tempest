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
__author__ = 'Albert'
__email__ = "albert.vico@midokura.com"

from tempest import clients
from tempest.common.utils import data_utils


class TenantAdmin(object):
    _interface = 'json'

    def __init__(self):
            os = clients.AdminManager(interface=self._interface)
            self.client = os.identity_client
            self.tenants = []

    def tenant_create_enabled(self):
        # Create a tenant that is enabled
        tenant_name = data_utils.rand_name(name='tenant-')
        description = data_utils.rand_name('desc_')
        resp, tenant = self.client.create_tenant(
            name=tenant_name,
            description=description, enabled=True)
        self.tenants.append(tenant)
        return tenant

    def get_tenant(self, tenant_id):
        res, tenant = self.client.get_tenant(tenant_id)
        self.tenants.append(tenant)
        return tenant

    def teardown_all(self):
            for tenant in self.tenants:
                self.client.delete_tenant(tenant['id'])
            self.tenants = []