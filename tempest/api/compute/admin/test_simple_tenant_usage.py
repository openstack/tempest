# Copyright 2013 NEC Corporation
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

import datetime
import time

from tempest.api.compute import base
from tempest import test


class TenantUsagesTestJSON(base.BaseV2ComputeAdminTest):

    @classmethod
    def setup_clients(cls):
        super(TenantUsagesTestJSON, cls).setup_clients()
        cls.adm_client = cls.os_adm.tenant_usages_client
        cls.client = cls.os.tenant_usages_client

    @classmethod
    def resource_setup(cls):
        super(TenantUsagesTestJSON, cls).resource_setup()
        cls.tenant_id = cls.client.tenant_id

        # Create a server in the demo tenant
        cls.create_test_server(wait_until='ACTIVE')
        time.sleep(2)

        now = datetime.datetime.now()
        cls.start = cls._parse_strtime(now - datetime.timedelta(days=1))
        cls.end = cls._parse_strtime(now + datetime.timedelta(days=1))

    @classmethod
    def _parse_strtime(cls, at):
        # Returns formatted datetime
        return at.strftime('%Y-%m-%dT%H:%M:%S.%f')

    @test.attr(type='gate')
    @test.idempotent_id('062c8ae9-9912-4249-8b51-e38d664e926e')
    def test_list_usage_all_tenants(self):
        # Get usage for all tenants
        params = {'start': self.start,
                  'end': self.end,
                  'detailed': int(bool(True))}
        tenant_usage = self.adm_client.list_tenant_usages(params)
        self.assertEqual(len(tenant_usage), 8)

    @test.attr(type='gate')
    @test.idempotent_id('94135049-a4c5-4934-ad39-08fa7da4f22e')
    def test_get_usage_tenant(self):
        # Get usage for a specific tenant
        params = {'start': self.start,
                  'end': self.end}
        tenant_usage = self.adm_client.get_tenant_usage(
            self.tenant_id, params)

        self.assertEqual(len(tenant_usage), 8)

    @test.attr(type='gate')
    @test.idempotent_id('9d00a412-b40e-4fd9-8eba-97b496316116')
    def test_get_usage_tenant_with_non_admin_user(self):
        # Get usage for a specific tenant with non admin user
        params = {'start': self.start,
                  'end': self.end}
        tenant_usage = self.client.get_tenant_usage(
            self.tenant_id, params)

        self.assertEqual(len(tenant_usage), 8)
