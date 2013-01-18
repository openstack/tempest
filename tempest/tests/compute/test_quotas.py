# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

from nose.plugins.attrib import attr

from tempest.tests.compute.base import BaseCompTest


class QuotasTest(BaseCompTest):

    @classmethod
    def setUpClass(cls):
        super(QuotasTest, cls).setUpClass()
        cls.client = cls.quotas_client
        cls.admin_client = cls._get_identity_admin_client()
        resp, tenants = cls.admin_client.list_tenants()
        cls.tenant_id = [tnt['id'] for tnt in tenants if tnt['name'] ==
                         cls.client.tenant_name][0]

    @attr(type='smoke')
    def test_get_default_quotas(self):
        # User can get the default quota set for it's tenant
        expected_quota_set = {'injected_file_content_bytes': 10240,
                              'metadata_items': 128, 'injected_files': 5,
                              'ram': 51200, 'floating_ips': 10,
                              'key_pairs': 100,
                              'injected_file_path_bytes': 255, 'instances': 10,
                              'security_group_rules': 20, 'cores': 20,
                              'id': self.tenant_id, 'security_groups': 10}
        try:
            resp, quota_set = self.client.get_quota_set(self.tenant_id)
            self.assertEqual(200, resp.status)
            self.assertSequenceEqual(expected_quota_set, quota_set)
        except Exception:
            self.fail("Quota set for tenant did not have default limits")
