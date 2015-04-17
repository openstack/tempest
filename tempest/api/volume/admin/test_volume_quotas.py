# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
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

from tempest_lib.common.utils import data_utils

from tempest.api.volume import base
from tempest import test

QUOTA_KEYS = ['gigabytes', 'snapshots', 'volumes']
QUOTA_USAGE_KEYS = ['reserved', 'limit', 'in_use']


class BaseVolumeQuotasAdminV2TestJSON(base.BaseVolumeAdminTest):
    force_tenant_isolation = True

    @classmethod
    def setup_credentials(cls):
        super(BaseVolumeQuotasAdminV2TestJSON, cls).setup_credentials()
        cls.demo_tenant_id = cls.isolated_creds.get_primary_creds().tenant_id

    @test.attr(type='gate')
    @test.idempotent_id('59eada70-403c-4cef-a2a3-a8ce2f1b07a0')
    def test_list_quotas(self):
        quotas = self.quotas_client.show_quota_set(self.demo_tenant_id)
        for key in QUOTA_KEYS:
            self.assertIn(key, quotas)

    @test.attr(type='gate')
    @test.idempotent_id('2be020a2-5fdd-423d-8d35-a7ffbc36e9f7')
    def test_list_default_quotas(self):
        quotas = self.quotas_client.show_default_quota_set(
            self.demo_tenant_id)
        for key in QUOTA_KEYS:
            self.assertIn(key, quotas)

    @test.attr(type='gate')
    @test.idempotent_id('3d45c99e-cc42-4424-a56e-5cbd212b63a6')
    def test_update_all_quota_resources_for_tenant(self):
        # Admin can update all the resource quota limits for a tenant
        default_quota_set = self.quotas_client.show_default_quota_set(
            self.demo_tenant_id)
        new_quota_set = {'gigabytes': 1009,
                         'volumes': 11,
                         'snapshots': 11}

        # Update limits for all quota resources
        quota_set = self.quotas_client.update_quota_set(
            self.demo_tenant_id,
            **new_quota_set)

        cleanup_quota_set = dict(
            (k, v) for k, v in default_quota_set.iteritems()
            if k in QUOTA_KEYS)
        self.addCleanup(self.quotas_client.update_quota_set,
                        self.demo_tenant_id, **cleanup_quota_set)
        # test that the specific values we set are actually in
        # the final result. There is nothing here that ensures there
        # would be no other values in there.
        self.assertDictContainsSubset(new_quota_set, quota_set)

    @test.attr(type='gate')
    @test.idempotent_id('18c51ae9-cb03-48fc-b234-14a19374dbed')
    def test_show_quota_usage(self):
        quota_usage = self.quotas_client.show_quota_usage(
            self.os_adm.credentials.tenant_id)
        for key in QUOTA_KEYS:
            self.assertIn(key, quota_usage)
            for usage_key in QUOTA_USAGE_KEYS:
                self.assertIn(usage_key, quota_usage[key])

    @test.attr(type='gate')
    @test.idempotent_id('ae8b6091-48ad-4bfa-a188-bbf5cc02115f')
    def test_quota_usage(self):
        quota_usage = self.quotas_client.show_quota_usage(
            self.demo_tenant_id)

        volume = self.create_volume()
        self.addCleanup(self.admin_volume_client.delete_volume,
                        volume['id'])

        new_quota_usage = self.quotas_client.show_quota_usage(
            self.demo_tenant_id)

        self.assertEqual(quota_usage['volumes']['in_use'] + 1,
                         new_quota_usage['volumes']['in_use'])

        self.assertEqual(quota_usage['gigabytes']['in_use'] +
                         volume["size"],
                         new_quota_usage['gigabytes']['in_use'])

    @test.attr(type='gate')
    @test.idempotent_id('874b35a9-51f1-4258-bec5-cd561b6690d3')
    def test_delete_quota(self):
        # Admin can delete the resource quota set for a tenant
        tenant_name = data_utils.rand_name('quota_tenant_')
        identity_client = self.os_adm.identity_client
        tenant = identity_client.create_tenant(tenant_name)
        tenant_id = tenant['id']
        self.addCleanup(identity_client.delete_tenant, tenant_id)
        quota_set_default = self.quotas_client.show_default_quota_set(
            tenant_id)
        volume_default = quota_set_default['volumes']

        self.quotas_client.update_quota_set(tenant_id,
                                            volumes=(int(volume_default) + 5))

        self.quotas_client.delete_quota_set(tenant_id)
        quota_set_new = self.quotas_client.show_quota_set(tenant_id)
        self.assertEqual(volume_default, quota_set_new['volumes'])


class VolumeQuotasAdminV1TestJSON(BaseVolumeQuotasAdminV2TestJSON):
    _api_version = 1
