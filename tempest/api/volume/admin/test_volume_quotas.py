# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Author: Sylvain Baubeau <sylvain.baubeau@enovance.com>
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

from tempest.api.volume import base
from tempest import test

QUOTA_KEYS = ['gigabytes', 'snapshots', 'volumes']
QUOTA_USAGE_KEYS = ['reserved', 'limit', 'in_use']


class VolumeQuotasAdminTestJSON(base.BaseVolumeV1AdminTest):
    _interface = "json"
    force_tenant_isolation = True

    @classmethod
    def setUpClass(cls):
        super(VolumeQuotasAdminTestJSON, cls).setUpClass()
        cls.admin_volume_client = cls.os_adm.volumes_client
        cls.demo_tenant_id = cls.isolated_creds.get_primary_user().get(
            'tenantId')

    @test.attr(type='gate')
    def test_list_quotas(self):
        resp, quotas = self.quotas_client.get_quota_set(self.demo_tenant_id)
        self.assertEqual(200, resp.status)
        for key in QUOTA_KEYS:
            self.assertIn(key, quotas)

    @test.attr(type='gate')
    def test_list_default_quotas(self):
        resp, quotas = self.quotas_client.get_default_quota_set(
            self.demo_tenant_id)
        self.assertEqual(200, resp.status)
        for key in QUOTA_KEYS:
            self.assertIn(key, quotas)

    @test.attr(type='gate')
    def test_update_all_quota_resources_for_tenant(self):
        # Admin can update all the resource quota limits for a tenant
        resp, default_quota_set = self.quotas_client.get_default_quota_set(
            self.demo_tenant_id)
        new_quota_set = {'gigabytes': 1009,
                         'volumes': 11,
                         'snapshots': 11}

        # Update limits for all quota resources
        resp, quota_set = self.quotas_client.update_quota_set(
            self.demo_tenant_id,
            **new_quota_set)

        default_quota_set.pop('id')
        self.addCleanup(self.quotas_client.update_quota_set,
                        self.demo_tenant_id, **default_quota_set)
        self.assertEqual(200, resp.status)
        self.assertEqual(new_quota_set, quota_set)

    @test.attr(type='gate')
    def test_show_quota_usage(self):
        resp, quota_usage = self.quotas_client.get_quota_usage(self.adm_tenant)
        self.assertEqual(200, resp.status)
        for key in QUOTA_KEYS:
            self.assertIn(key, quota_usage)
            for usage_key in QUOTA_USAGE_KEYS:
                self.assertIn(usage_key, quota_usage[key])

    @test.attr(type='gate')
    def test_quota_usage(self):
        resp, quota_usage = self.quotas_client.get_quota_usage(
            self.demo_tenant_id)

        volume = self.create_volume(size=1)
        self.addCleanup(self.admin_volume_client.delete_volume,
                        volume['id'])

        resp, new_quota_usage = self.quotas_client.get_quota_usage(
            self.demo_tenant_id)

        self.assertEqual(200, resp.status)
        self.assertEqual(quota_usage['volumes']['in_use'] + 1,
                         new_quota_usage['volumes']['in_use'])

        self.assertEqual(quota_usage['gigabytes']['in_use'] + 1,
                         new_quota_usage['gigabytes']['in_use'])


class VolumeQuotasAdminTestXML(VolumeQuotasAdminTestJSON):
    _interface = "xml"
