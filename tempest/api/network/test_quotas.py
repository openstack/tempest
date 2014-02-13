# Copyright 2013 OpenStack Foundation
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


from tempest.api.network import base
from tempest import clients
from tempest.common.utils import data_utils
from tempest import test


class QuotasTest(base.BaseNetworkTest):
    _interface = 'json'

    """
    Tests the following operations in the Neutron API using the REST client for
    Neutron:

        list quotas for tenants who have non-default quota values
        show quotas for a specified tenant
        update quotas for a specified tenant
        reset quotas to default values for a specified tenant

    v2.0 of the API is assumed. It is also assumed that the following
    option is defined in the [service_available] section of etc/tempest.conf:

        neutron as True

    Finally, it is assumed that the per-tenant quota extension API is
    configured in /etc/neutron/neutron.conf as follows:

        quota_driver = neutron.db.quota_db.DbQuotaDriver
    """

    @classmethod
    def setUpClass(cls):
        super(QuotasTest, cls).setUpClass()
        if not test.is_extension_enabled('quotas', 'network'):
            msg = "quotas extension not enabled."
            raise cls.skipException(msg)
        admin_manager = clients.AdminManager()
        cls.admin_client = admin_manager.network_client
        cls.identity_admin_client = admin_manager.identity_client

    @test.attr(type='gate')
    def test_quotas(self):
        # Add a tenant to conduct the test
        test_tenant = data_utils.rand_name('test_tenant_')
        test_description = data_utils.rand_name('desc_')
        _, tenant = self.identity_admin_client.create_tenant(
            name=test_tenant,
            description=test_description)
        tenant_id = tenant['id']
        self.addCleanup(self.identity_admin_client.delete_tenant, tenant_id)
        # Change quotas for tenant
        new_quotas = {'network': 0, 'security_group': 0}
        resp, quota_set = self.admin_client.update_quotas(tenant_id,
                                                          **new_quotas)
        self.assertEqual('200', resp['status'])
        self.addCleanup(self.admin_client.reset_quotas, tenant_id)
        self.assertEqual(0, quota_set['network'])
        self.assertEqual(0, quota_set['security_group'])
        # Confirm our tenant is listed among tenants with non default quotas
        resp, non_default_quotas = self.admin_client.list_quotas()
        self.assertEqual('200', resp['status'])
        found = False
        for qs in non_default_quotas['quotas']:
            if qs['tenant_id'] == tenant_id:
                found = True
        self.assertTrue(found)
        # Confirm from APi quotas were changed as requested for tenant
        resp, quota_set = self.admin_client.show_quotas(tenant_id)
        quota_set = quota_set['quota']
        self.assertEqual('200', resp['status'])
        self.assertEqual(0, quota_set['network'])
        self.assertEqual(0, quota_set['security_group'])
        # Reset quotas to default and confirm
        resp, body = self.admin_client.reset_quotas(tenant_id)
        self.assertEqual('204', resp['status'])
        resp, non_default_quotas = self.admin_client.list_quotas()
        self.assertEqual('200', resp['status'])
        for q in non_default_quotas['quotas']:
            self.assertNotEqual(tenant_id, q['tenant_id'])
