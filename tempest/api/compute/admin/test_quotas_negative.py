# Copyright 2014 NEC Corporation.  All rights reserved.
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
from tempest.common.utils import data_utils
from tempest import config
from tempest import exceptions
from tempest import test

CONF = config.CONF


class QuotasAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):
    force_tenant_isolation = True

    @classmethod
    def setUpClass(cls):
        super(QuotasAdminNegativeTestJSON, cls).setUpClass()
        cls.client = cls.os.quotas_client
        cls.adm_client = cls.os_adm.quotas_client
        cls.sg_client = cls.security_groups_client

        # NOTE(afazekas): these test cases should always create and use a new
        # tenant most of them should be skipped if we can't do that
        cls.demo_tenant_id = cls.isolated_creds.get_primary_user().get(
            'tenantId')

    @test.attr(type=['negative', 'gate'])
    def test_update_quota_normal_user(self):
        self.assertRaises(exceptions.Unauthorized,
                          self.client.update_quota_set,
                          self.demo_tenant_id,
                          ram=0)

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

    @test.skip_because(bug="1186354",
                       condition=CONF.service_available.neutron)
    @test.attr(type='gate')
    def test_security_groups_exceed_limit(self):
        # Negative test: Creation Security Groups over limit should FAIL

        resp, quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_sg_quota = quota_set['security_groups']
        sg_quota = 0  # Set the quota to zero to conserve resources

        resp, quota_set =\
            self.adm_client.update_quota_set(self.demo_tenant_id,
                                             force=True,
                                             security_groups=sg_quota)

        self.addCleanup(self.adm_client.update_quota_set,
                        self.demo_tenant_id,
                        security_groups=default_sg_quota)

        # Check we cannot create anymore
        self.assertRaises(exceptions.OverLimit,
                          self.sg_client.create_security_group,
                          "sg-overlimit", "sg-desc")

    @test.skip_because(bug="1186354",
                       condition=CONF.service_available.neutron)
    @test.attr(type=['negative', 'gate'])
    def test_security_groups_rules_exceed_limit(self):
        # Negative test: Creation of Security Group Rules should FAIL
        # when we reach limit maxSecurityGroupRules

        resp, quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_sg_rules_quota = quota_set['security_group_rules']
        sg_rules_quota = 0  # Set the quota to zero to conserve resources

        resp, quota_set =\
            self.adm_client.update_quota_set(
                self.demo_tenant_id,
                force=True,
                security_group_rules=sg_rules_quota)

        self.addCleanup(self.adm_client.update_quota_set,
                        self.demo_tenant_id,
                        security_group_rules=default_sg_rules_quota)

        s_name = data_utils.rand_name('securitygroup-')
        s_description = data_utils.rand_name('description-')
        resp, securitygroup =\
            self.sg_client.create_security_group(s_name, s_description)
        self.addCleanup(self.sg_client.delete_security_group,
                        securitygroup['id'])

        secgroup_id = securitygroup['id']
        ip_protocol = 'tcp'

        # Check we cannot create SG rule anymore
        self.assertRaises(exceptions.OverLimit,
                          self.sg_client.create_security_group_rule,
                          secgroup_id, ip_protocol, 1025, 1025)


class QuotasAdminNegativeTestXML(QuotasAdminNegativeTestJSON):
    _interface = 'xml'
