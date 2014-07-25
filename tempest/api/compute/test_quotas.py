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

from tempest.api.compute import base
from tempest.common import tempest_fixtures as fixtures
from tempest import test


class QuotasTestJSON(base.BaseV2ComputeTest):

    def setUp(self):
        # NOTE(mriedem): Avoid conflicts with os-quota-class-sets tests.
        self.useFixture(fixtures.LockFixture('compute_quotas'))
        super(QuotasTestJSON, self).setUp()

    @classmethod
    def setUpClass(cls):
        super(QuotasTestJSON, cls).setUpClass()
        cls.client = cls.quotas_client
        cls.tenant_id = cls.client.tenant_id
        cls.user_id = cls.client.user_id
        cls.default_quota_set = set(('injected_file_content_bytes',
                                     'metadata_items', 'injected_files',
                                     'ram', 'floating_ips',
                                     'fixed_ips', 'key_pairs',
                                     'injected_file_path_bytes',
                                     'instances', 'security_group_rules',
                                     'cores', 'security_groups'))

    @test.attr(type='smoke')
    def test_get_quotas(self):
        # User can get the quota set for it's tenant
        expected_quota_set = self.default_quota_set | set(['id'])
        resp, quota_set = self.client.get_quota_set(self.tenant_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(sorted(expected_quota_set),
                         sorted(quota_set.keys()))
        self.assertEqual(quota_set['id'], self.tenant_id)

        # get the quota set using user id
        resp, quota_set = self.client.get_quota_set(self.tenant_id,
                                                    self.user_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(sorted(expected_quota_set),
                         sorted(quota_set.keys()))
        self.assertEqual(quota_set['id'], self.tenant_id)

    @test.attr(type='smoke')
    def test_get_default_quotas(self):
        # User can get the default quota set for it's tenant
        expected_quota_set = self.default_quota_set | set(['id'])
        resp, quota_set = self.client.get_default_quota_set(self.tenant_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(sorted(expected_quota_set),
                         sorted(quota_set.keys()))
        self.assertEqual(quota_set['id'], self.tenant_id)

    @test.attr(type='smoke')
    def test_compare_tenant_quotas_with_default_quotas(self):
        # Tenants are created with the default quota values
        resp, defualt_quota_set = \
            self.client.get_default_quota_set(self.tenant_id)
        self.assertEqual(200, resp.status)
        resp, tenant_quota_set = self.client.get_quota_set(self.tenant_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(defualt_quota_set, tenant_quota_set)


class QuotasTestXML(QuotasTestJSON):
    _interface = 'xml'
