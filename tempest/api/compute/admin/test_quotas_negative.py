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

from tempest_lib.common.utils import data_utils
from tempest_lib import decorators
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class QuotasAdminNegativeTestJSON(base.BaseV2ComputeAdminTest):
    force_tenant_isolation = True

    @classmethod
    def setup_clients(cls):
        super(QuotasAdminNegativeTestJSON, cls).setup_clients()
        cls.client = cls.os.quotas_client
        cls.adm_client = cls.os_adm.quotas_client
        cls.sg_client = cls.security_groups_client

    @classmethod
    def resource_setup(cls):
        super(QuotasAdminNegativeTestJSON, cls).resource_setup()
        # NOTE(afazekas): these test cases should always create and use a new
        # tenant most of them should be skipped if we can't do that
        cls.demo_tenant_id = cls.client.tenant_id

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('733abfe8-166e-47bb-8363-23dbd7ff3476')
    def test_update_quota_normal_user(self):
        self.assertRaises(lib_exc.Forbidden,
                          self.client.update_quota_set,
                          self.demo_tenant_id,
                          ram=0)

    # TODO(afazekas): Add dedicated tenant to the skiped quota tests
    # it can be moved into the setUpClass as well
    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('91058876-9947-4807-9f22-f6eb17140d9b')
    def test_create_server_when_cpu_quota_is_full(self):
        # Disallow server creation when tenant's vcpu quota is full
        quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_vcpu_quota = quota_set['cores']
        vcpu_quota = 0  # Set the quota to zero to conserve resources

        quota_set = self.adm_client.update_quota_set(self.demo_tenant_id,
                                                     force=True,
                                                     cores=vcpu_quota)

        self.addCleanup(self.adm_client.update_quota_set, self.demo_tenant_id,
                        cores=default_vcpu_quota)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.create_test_server)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('6fdd7012-584d-4327-a61c-49122e0d5864')
    def test_create_server_when_memory_quota_is_full(self):
        # Disallow server creation when tenant's memory quota is full
        quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_mem_quota = quota_set['ram']
        mem_quota = 0  # Set the quota to zero to conserve resources

        self.adm_client.update_quota_set(self.demo_tenant_id,
                                         force=True,
                                         ram=mem_quota)

        self.addCleanup(self.adm_client.update_quota_set, self.demo_tenant_id,
                        ram=default_mem_quota)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.create_test_server)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('7c6be468-0274-449a-81c3-ac1c32ee0161')
    def test_create_server_when_instances_quota_is_full(self):
        # Once instances quota limit is reached, disallow server creation
        quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_instances_quota = quota_set['instances']
        instances_quota = 0  # Set quota to zero to disallow server creation

        self.adm_client.update_quota_set(self.demo_tenant_id,
                                         force=True,
                                         instances=instances_quota)
        self.addCleanup(self.adm_client.update_quota_set, self.demo_tenant_id,
                        instances=default_instances_quota)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.create_test_server)

    @decorators.skip_because(bug="1186354",
                             condition=CONF.service_available.neutron)
    @test.attr(type='gate')
    @test.idempotent_id('7c6c8f3b-2bf6-4918-b240-57b136a66aa0')
    @test.services('network')
    def test_security_groups_exceed_limit(self):
        # Negative test: Creation Security Groups over limit should FAIL

        quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_sg_quota = quota_set['security_groups']
        sg_quota = 0  # Set the quota to zero to conserve resources

        quota_set =\
            self.adm_client.update_quota_set(self.demo_tenant_id,
                                             force=True,
                                             security_groups=sg_quota)

        self.addCleanup(self.adm_client.update_quota_set,
                        self.demo_tenant_id,
                        security_groups=default_sg_quota)

        # Check we cannot create anymore
        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised when out of quota
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.sg_client.create_security_group,
                          "sg-overlimit", "sg-desc")

    @decorators.skip_because(bug="1186354",
                             condition=CONF.service_available.neutron)
    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('6e9f436d-f1ed-4f8e-a493-7275dfaa4b4d')
    @test.services('network')
    def test_security_groups_rules_exceed_limit(self):
        # Negative test: Creation of Security Group Rules should FAIL
        # when we reach limit maxSecurityGroupRules

        quota_set = self.adm_client.get_quota_set(self.demo_tenant_id)
        default_sg_rules_quota = quota_set['security_group_rules']
        sg_rules_quota = 0  # Set the quota to zero to conserve resources

        quota_set =\
            self.adm_client.update_quota_set(
                self.demo_tenant_id,
                force=True,
                security_group_rules=sg_rules_quota)

        self.addCleanup(self.adm_client.update_quota_set,
                        self.demo_tenant_id,
                        security_group_rules=default_sg_rules_quota)

        s_name = data_utils.rand_name('securitygroup')
        s_description = data_utils.rand_name('description')
        securitygroup =\
            self.sg_client.create_security_group(s_name, s_description)
        self.addCleanup(self.sg_client.delete_security_group,
                        securitygroup['id'])

        secgroup_id = securitygroup['id']
        ip_protocol = 'tcp'

        # Check we cannot create SG rule anymore
        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised when out of quota
        self.assertRaises((lib_exc.OverLimit, lib_exc.Forbidden),
                          self.sg_client.create_security_group_rule,
                          secgroup_id, ip_protocol, 1025, 1025)
