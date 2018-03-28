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
from tempest.common import utils
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class QuotasAdminNegativeTestBase(base.BaseV2ComputeAdminTest):
    force_tenant_isolation = True

    @classmethod
    def setup_clients(cls):
        super(QuotasAdminNegativeTestBase, cls).setup_clients()
        cls.client = cls.os_primary.quotas_client
        cls.adm_client = cls.os_admin.quotas_client
        cls.sg_client = cls.security_groups_client
        cls.sgr_client = cls.security_group_rules_client

    @classmethod
    def resource_setup(cls):
        super(QuotasAdminNegativeTestBase, cls).resource_setup()
        # NOTE(afazekas): these test cases should always create and use a new
        # tenant most of them should be skipped if we can't do that
        cls.demo_tenant_id = cls.client.tenant_id

    def _update_quota(self, quota_item, quota_value):
        quota_set = (self.adm_client.show_quota_set(self.demo_tenant_id)
                     ['quota_set'])
        default_quota_value = quota_set[quota_item]

        self.adm_client.update_quota_set(self.demo_tenant_id,
                                         force=True,
                                         **{quota_item: quota_value})
        self.addCleanup(self.adm_client.update_quota_set, self.demo_tenant_id,
                        **{quota_item: default_quota_value})


class QuotasAdminNegativeTest(QuotasAdminNegativeTestBase):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('733abfe8-166e-47bb-8363-23dbd7ff3476')
    def test_update_quota_normal_user(self):
        self.assertRaises(lib_exc.Forbidden,
                          self.client.update_quota_set,
                          self.demo_tenant_id,
                          ram=0)

    # TODO(afazekas): Add dedicated tenant to the skipped quota tests.
    # It can be moved into the setUpClass as well.
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('91058876-9947-4807-9f22-f6eb17140d9b')
    def test_create_server_when_cpu_quota_is_full(self):
        # Disallow server creation when tenant's vcpu quota is full
        self._update_quota('cores', 0)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.create_test_server)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('6fdd7012-584d-4327-a61c-49122e0d5864')
    def test_create_server_when_memory_quota_is_full(self):
        # Disallow server creation when tenant's memory quota is full
        self._update_quota('ram', 0)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.create_test_server)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7c6be468-0274-449a-81c3-ac1c32ee0161')
    def test_create_server_when_instances_quota_is_full(self):
        # Once instances quota limit is reached, disallow server creation
        self._update_quota('instances', 0)
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.create_test_server)


class QuotasSecurityGroupAdminNegativeTest(QuotasAdminNegativeTestBase):
    max_microversion = '2.35'

    @decorators.skip_because(bug="1186354",
                             condition=CONF.service_available.neutron)
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('7c6c8f3b-2bf6-4918-b240-57b136a66aa0')
    @utils.services('network')
    def test_security_groups_exceed_limit(self):
        # Negative test: Creation Security Groups over limit should FAIL
        # Set the quota to number of used security groups
        sg_quota = self.limits_client.show_limits()['limits']['absolute'][
            'totalSecurityGroupsUsed']
        self._update_quota('security_groups', sg_quota)

        # Check we cannot create anymore
        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised when out of quota
        self.assertRaises((lib_exc.Forbidden, lib_exc.OverLimit),
                          self.sg_client.create_security_group,
                          name="sg-overlimit", description="sg-desc")

    @decorators.skip_because(bug="1186354",
                             condition=CONF.service_available.neutron)
    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('6e9f436d-f1ed-4f8e-a493-7275dfaa4b4d')
    @utils.services('network')
    def test_security_groups_rules_exceed_limit(self):
        # Negative test: Creation of Security Group Rules should FAIL
        # when we reach limit maxSecurityGroupRules
        self._update_quota('security_group_rules', 0)

        s_name = data_utils.rand_name('securitygroup')
        s_description = data_utils.rand_name('description')
        securitygroup = self.sg_client.create_security_group(
            name=s_name, description=s_description)['security_group']
        self.addCleanup(self.sg_client.delete_security_group,
                        securitygroup['id'])

        secgroup_id = securitygroup['id']
        ip_protocol = 'tcp'

        # Check we cannot create SG rule anymore
        # A 403 Forbidden or 413 Overlimit (old behaviour) exception
        # will be raised when out of quota
        self.assertRaises((lib_exc.OverLimit, lib_exc.Forbidden),
                          self.sgr_client.create_security_group_rule,
                          parent_group_id=secgroup_id, ip_protocol=ip_protocol,
                          from_port=1025, to_port=1025)
