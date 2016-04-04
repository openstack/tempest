# Copyright 2015 Cloudwatt
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
from tempest.lib import exceptions as lib_exc
from tempest import test


class QuotasNegativeTest(base.BaseAdminNetworkTest):
    """Tests the following operations in the Neutron API:

        set network quota and exceed this quota

    v2.0 of the API is assumed.
    It is also assumed that the per-project quota extension API is configured
    in /etc/neutron/neutron.conf as follows:

        quota_driver = neutron.db.quota_db.DbQuotaDriver
    """
    force_tenant_isolation = True

    @classmethod
    def skip_checks(cls):
        super(QuotasNegativeTest, cls).skip_checks()
        if not test.is_extension_enabled('quotas', 'network'):
            msg = "quotas extension not enabled."
            raise cls.skipException(msg)

    @classmethod
    def setup_clients(cls):
        super(QuotasNegativeTest, cls).setup_clients()
        cls.identity_admin_client = cls.os_adm.identity_client

    @test.idempotent_id('644f4e1b-1bf9-4af0-9fd8-eb56ac0f51cf')
    def test_network_quota_exceeding(self):
        # Set the network quota to two
        self.admin_quotas_client.update_quotas(self.networks_client.tenant_id,
                                               network=2)
        self.addCleanup(self.admin_quotas_client.reset_quotas,
                        self.networks_client.tenant_id)

        # Create two networks
        n1 = self.networks_client.create_network()
        self.addCleanup(self.networks_client.delete_network,
                        n1['network']['id'])
        n2 = self.networks_client.create_network()
        self.addCleanup(self.networks_client.delete_network,
                        n2['network']['id'])

        # Try to create a third network while the quota is two
        with self.assertRaisesRegex(
                lib_exc.Conflict,
                "An object with that identifier already exists\\n" +
                "Details.*Quota exceeded for resources: \['network'\].*"):
            n3 = self.networks_client.create_network()
            self.addCleanup(self.networks_client.delete_network,
                            n3['network']['id'])
