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

from tempest.api.compute import base
from tempest import test
import time


class TenantUsagesTestJSON(base.BaseV2ComputeAdminTest):

    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(TenantUsagesTestJSON, cls).setUpClass()
        cls.adm_client = cls.os_adm.tenant_usages_client
        cls.client = cls.os.tenant_usages_client
        cls.identity_client = cls._get_identity_admin_client()

        resp, tenants = cls.identity_client.list_tenants()
        cls.tenant_id = [tnt['id'] for tnt in tenants if tnt['name'] ==
                         cls.client.tenant_name][0]

        # Create a server in the demo tenant
        resp, server = cls.create_test_server(wait_until='ACTIVE')
        time.sleep(2)

        now = datetime.datetime.now()
        cls.start = cls._parse_strtime(now - datetime.timedelta(days=1))
        cls.end = cls._parse_strtime(now + datetime.timedelta(days=1))

    @classmethod
    def _parse_strtime(cls, at):
        # Returns formatted datetime
        return at.strftime('%Y-%m-%dT%H:%M:%S.%f')

    @test.attr(type='gate')
    def test_list_usage_all_tenants(self):
        # Get usage for all tenants
        params = {'start': self.start,
                  'end': self.end,
                  'detailed': int(bool(True))}
        resp, tenant_usage = self.adm_client.list_tenant_usages(params)
        self.assertEqual(200, resp.status)
        self.assertEqual(len(tenant_usage), 8)

    @test.attr(type='gate')
    def test_get_usage_tenant(self):
        # Get usage for a specific tenant
        params = {'start': self.start,
                  'end': self.end}
        resp, tenant_usage = self.adm_client.get_tenant_usage(
            self.tenant_id, params)

        self.assertEqual(200, resp.status)
        self.assertEqual(len(tenant_usage), 8)

    @test.attr(type='gate')
    def test_get_usage_tenant_with_non_admin_user(self):
        # Get usage for a specific tenant with non admin user
        params = {'start': self.start,
                  'end': self.end}
        resp, tenant_usage = self.client.get_tenant_usage(
            self.tenant_id, params)

        self.assertEqual(200, resp.status)
        self.assertEqual(len(tenant_usage), 8)


class TenantUsagesTestXML(TenantUsagesTestJSON):
    _interface = 'xml'
