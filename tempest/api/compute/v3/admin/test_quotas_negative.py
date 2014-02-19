# Copyright 2013 OpenStack Foundation
# Copyright 2014 NEC Corporation
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
from tempest import exceptions
from tempest import test


class QuotasAdminNegativeV3Test(base.BaseV3ComputeAdminTest):
    _interface = 'json'
    force_tenant_isolation = True

    @classmethod
    def setUpClass(cls):
        super(QuotasAdminNegativeV3Test, cls).setUpClass()
        cls.client = cls.quotas_client
        cls.adm_client = cls.quotas_admin_client

        # NOTE(afazekas): these test cases should always create and use a new
        # tenant most of them should be skipped if we can't do that
        cls.demo_tenant_id = cls.isolated_creds.get_primary_user().get(
            'tenantId')

    # TODO(afazekas): Add dedicated tenant to the skiped quota tests
    # it can be moved into the setUpClass as well
    @test.attr(type=['negative', 'gate'])
    def test_create_server_when_cpu_quota_is_full(self):
        # Disallow server creation when tenant's vcpu quota is full
        resp, quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_vcpu_quota = quota_set['cores']
        vcpu_quota = 0  # Set the quota to zero to conserve resources

        resp, quota_set = self.adm_client.update_quota_set(self.demo_tenant_id,
                                                           force=True,
                                                           cores=vcpu_quota)

        self.addCleanup(self.adm_client.update_quota_set, self.demo_tenant_id,
                        cores=default_vcpu_quota)
        self.assertRaises(exceptions.OverLimit, self.create_test_server)

    @test.attr(type=['negative', 'gate'])
    def test_create_server_when_memory_quota_is_full(self):
        # Disallow server creation when tenant's memory quota is full
        resp, quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_mem_quota = quota_set['ram']
        mem_quota = 0  # Set the quota to zero to conserve resources

        self.adm_client.update_quota_set(self.demo_tenant_id,
                                         force=True,
                                         ram=mem_quota)

        self.addCleanup(self.adm_client.update_quota_set, self.demo_tenant_id,
                        ram=default_mem_quota)
        self.assertRaises(exceptions.OverLimit, self.create_test_server)

    @test.attr(type=['negative', 'gate'])
    def test_update_quota_normal_user(self):
        self.assertRaises(exceptions.Unauthorized,
                          self.client.update_quota_set,
                          self.demo_tenant_id,
                          ram=0)

    @test.attr(type=['negative', 'gate'])
    def test_create_server_when_instances_quota_is_full(self):
        # Once instances quota limit is reached, disallow server creation
        resp, quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_instances_quota = quota_set['instances']
        instances_quota = 0  # Set quota to zero to disallow server creation

        self.adm_client.update_quota_set(self.demo_tenant_id,
                                         force=True,
                                         instances=instances_quota)
        self.addCleanup(self.adm_client.update_quota_set, self.demo_tenant_id,
                        instances=default_instances_quota)
        self.assertRaises(exceptions.OverLimit, self.create_test_server)
