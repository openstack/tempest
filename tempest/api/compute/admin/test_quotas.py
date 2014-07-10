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

import six
from testtools import matchers

from tempest.api.compute import base
from tempest.common import tempest_fixtures as fixtures
from tempest.common.utils import data_utils
from tempest.openstack.common import log as logging
from tempest import test

LOG = logging.getLogger(__name__)


class QuotasAdminTestJSON(base.BaseV2ComputeAdminTest):
    force_tenant_isolation = True

    def setUp(self):
        # NOTE(mriedem): Avoid conflicts with os-quota-class-sets tests.
        self.useFixture(fixtures.LockFixture('compute_quotas'))
        super(QuotasAdminTestJSON, self).setUp()

    @classmethod
    def setUpClass(cls):
        super(QuotasAdminTestJSON, cls).setUpClass()
        cls.adm_client = cls.os_adm.quotas_client

        # NOTE(afazekas): these test cases should always create and use a new
        # tenant most of them should be skipped if we can't do that
        cls.demo_tenant_id = cls.quotas_client.tenant_id

        cls.default_quota_set = set(('injected_file_content_bytes',
                                     'metadata_items', 'injected_files',
                                     'ram', 'floating_ips',
                                     'fixed_ips', 'key_pairs',
                                     'injected_file_path_bytes',
                                     'instances', 'security_group_rules',
                                     'cores', 'security_groups'))

    @test.attr(type='smoke')
    def test_get_default_quotas(self):
        # Admin can get the default resource quota set for a tenant
        expected_quota_set = self.default_quota_set | set(['id'])
        resp, quota_set = self.adm_client.get_default_quota_set(
            self.demo_tenant_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(sorted(expected_quota_set),
                         sorted(quota_set.keys()))
        self.assertEqual(quota_set['id'], self.demo_tenant_id)

    @test.attr(type='gate')
    def test_update_all_quota_resources_for_tenant(self):
        # Admin can update all the resource quota limits for a tenant
        resp, default_quota_set = self.adm_client.get_default_quota_set(
            self.demo_tenant_id)
        new_quota_set = {'injected_file_content_bytes': 20480,
                         'metadata_items': 256, 'injected_files': 10,
                         'ram': 10240, 'floating_ips': 20, 'fixed_ips': 10,
                         'key_pairs': 200, 'injected_file_path_bytes': 512,
                         'instances': 20, 'security_group_rules': 20,
                         'cores': 2, 'security_groups': 20}
        # Update limits for all quota resources
        resp, quota_set = self.adm_client.update_quota_set(
            self.demo_tenant_id,
            force=True,
            **new_quota_set)

        default_quota_set.pop('id')
        self.addCleanup(self.adm_client.update_quota_set,
                        self.demo_tenant_id, **default_quota_set)
        self.assertEqual(200, resp.status)
        self.assertEqual(new_quota_set, quota_set)

    # TODO(afazekas): merge these test cases
    @test.attr(type='gate')
    def test_get_updated_quotas(self):
        # Verify that GET shows the updated quota set of tenant
        tenant_name = data_utils.rand_name('cpu_quota_tenant_')
        tenant_desc = tenant_name + '-desc'
        identity_client = self.os_adm.identity_client
        _, tenant = identity_client.create_tenant(name=tenant_name,
                                                  description=tenant_desc)
        tenant_id = tenant['id']
        self.addCleanup(identity_client.delete_tenant, tenant_id)

        self.adm_client.update_quota_set(tenant_id, ram='5120')
        resp, quota_set = self.adm_client.get_quota_set(tenant_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(5120, quota_set['ram'])

        # Verify that GET shows the updated quota set of user
        user_name = data_utils.rand_name('cpu_quota_user_')
        password = data_utils.rand_name('password-')
        email = user_name + '@testmail.tm'
        _, user = identity_client.create_user(name=user_name,
                                              password=password,
                                              tenant_id=tenant_id,
                                              email=email)
        user_id = user['id']
        self.addCleanup(identity_client.delete_user, user_id)

        self.adm_client.update_quota_set(tenant_id,
                                         user_id=user_id,
                                         ram='2048')
        resp, quota_set = self.adm_client.get_quota_set(tenant_id,
                                                        user_id=user_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(2048, quota_set['ram'])

    @test.attr(type='gate')
    def test_delete_quota(self):
        # Admin can delete the resource quota set for a tenant
        tenant_name = data_utils.rand_name('ram_quota_tenant_')
        tenant_desc = tenant_name + '-desc'
        identity_client = self.os_adm.identity_client
        _, tenant = identity_client.create_tenant(name=tenant_name,
                                                  description=tenant_desc)
        tenant_id = tenant['id']
        self.addCleanup(identity_client.delete_tenant, tenant_id)
        resp, quota_set_default = self.adm_client.get_quota_set(tenant_id)
        ram_default = quota_set_default['ram']

        resp, body = self.adm_client.update_quota_set(tenant_id, ram='5120')
        self.assertEqual(200, resp.status)

        resp, body = self.adm_client.delete_quota_set(tenant_id)
        self.assertEqual(202, resp.status)

        resp, quota_set_new = self.adm_client.get_quota_set(tenant_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(ram_default, quota_set_new['ram'])


class QuotasAdminTestXML(QuotasAdminTestJSON):
    _interface = 'xml'


class QuotaClassesAdminTestJSON(base.BaseV2ComputeAdminTest):
    """Tests the os-quota-class-sets API to update default quotas.
    """

    def setUp(self):
        # All test cases in this class need to externally lock on doing
        # anything with default quota values.
        self.useFixture(fixtures.LockFixture('compute_quotas'))
        super(QuotaClassesAdminTestJSON, self).setUp()

    @classmethod
    def setUpClass(cls):
        super(QuotaClassesAdminTestJSON, cls).setUpClass()
        cls.adm_client = cls.os_adm.quota_classes_client

    def _restore_default_quotas(self, original_defaults):
        LOG.debug("restoring quota class defaults")
        resp, body = self.adm_client.update_quota_class_set(
            'default', **original_defaults)
        self.assertEqual(200, resp.status)

    # NOTE(sdague): this test is problematic as it changes
    # global state, and possibly needs to be part of a set of
    # tests that get run all by themselves at the end under a
    # 'danger' flag.
    def test_update_default_quotas(self):
        LOG.debug("get the current 'default' quota class values")
        resp, body = self.adm_client.get_quota_class_set('default')
        self.assertEqual(200, resp.status)
        self.assertIn('id', body)
        self.assertEqual('default', body.pop('id'))
        # restore the defaults when the test is done
        self.addCleanup(self._restore_default_quotas, body.copy())
        # increment all of the values for updating the default quota class
        for quota, default in six.iteritems(body):
            # NOTE(sdague): we need to increment a lot, otherwise
            # there is a real chance that we go from -1 (unlimitted)
            # to a very small number which causes issues.
            body[quota] = default + 100
        LOG.debug("update limits for the default quota class set")
        resp, update_body = self.adm_client.update_quota_class_set('default',
                                                                   **body)
        self.assertEqual(200, resp.status)
        LOG.debug("assert that the response has all of the changed values")
        self.assertThat(update_body.items(),
                        matchers.ContainsAll(body.items()))


class QuotaClassesAdminTestXML(QuotaClassesAdminTestJSON):
    _interface = 'xml'
