# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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

import random

from oslo_log import log as logging
from testtools import matchers

from tempest.api.volume import base
from tempest.common import identity
from tempest.common import tempest_fixtures as fixtures
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

LOG = logging.getLogger(__name__)
QUOTA_KEYS = ['gigabytes', 'snapshots', 'volumes', 'backups',
              'backup_gigabytes', 'per_volume_gigabytes']


class VolumeQuotaClassesTest(base.BaseVolumeAdminTest):
    """Test volume quota classes"""

    def setUp(self):
        # Note(jeremy.zhang): All test cases in this class need to externally
        # lock on doing anything with default quota values.
        self.useFixture(fixtures.LockFixture('volume_quotas'))
        super(VolumeQuotaClassesTest, self).setUp()

    def _restore_default_quotas(self, original_defaults):
        LOG.debug("Restoring volume quota class defaults")
        self.admin_quota_classes_client.update_quota_class_set(
            'default', **original_defaults)

    @decorators.idempotent_id('abb9198e-67d0-4b09-859f-4f4a1418f176')
    def test_show_default_quota(self):
        """Test showing default volume quota class set"""
        # response body is validated by schema
        default_quotas = self.admin_quota_classes_client.show_quota_class_set(
            'default')['quota_class_set']
        self.assertEqual('default', default_quotas.pop('id'))

    @decorators.idempotent_id('a7644c63-2669-467a-b00e-452dd5c5397b')
    def test_update_default_quota(self):
        """Test updating default volume quota class set

        Check current project and new project's default quota are updated
        to the provided one.
        """
        LOG.debug("Get the current default quota class values")
        body = self.admin_quota_classes_client.show_quota_class_set(
            'default')['quota_class_set']

        # Note(jeremyZ) Only include specified quota keys to avoid the conflict
        # that other tests may create/delete volume types or update volume
        # type's default quotas in concurrency running.
        update_kwargs = {key: body[key] for key in body if key in QUOTA_KEYS}

        # Restore the defaults when the test is done.
        self.addCleanup(self._restore_default_quotas, update_kwargs.copy())

        # Note(jeremyZ) Increment some of the values for updating the default
        # quota class. For safety, only items with value >= 0 will be updated,
        # and items with value < 0 (-1 means unlimited) will be ignored.
        for quota, default in update_kwargs.items():
            if default >= 0:
                update_kwargs[quota] = default + 1

        # Create a volume type for updating default quotas class.
        volume_type_name = self.create_volume_type()['name']
        for key in ['volumes', 'snapshots', 'gigabytes']:
            update_kwargs['%s_%s' % (key, volume_type_name)] = \
                random.randint(1, 10)

        LOG.debug("Update limits for the default quota class set")
        update_body = self.admin_quota_classes_client.update_quota_class_set(
            'default', **update_kwargs)['quota_class_set']
        self.assertThat(update_body.items(),
                        matchers.ContainsAll(update_kwargs.items()))

        # Verify current project's default quotas.
        default_quotas = self.admin_quotas_client.show_default_quota_set(
            self.os_admin.credentials.tenant_id)['quota_set']
        self.assertThat(default_quotas.items(),
                        matchers.ContainsAll(update_kwargs.items()))

        # Verify a new project's default quotas.
        project_name = data_utils.rand_name('quota_class_tenant')
        description = data_utils.rand_name('desc_')
        project_id = identity.identity_utils(self.os_admin).create_project(
            name=project_name, description=description)['id']
        self.addCleanup(identity.identity_utils(self.os_admin).delete_project,
                        project_id)
        default_quotas = self.admin_quotas_client.show_default_quota_set(
            project_id)['quota_set']
        self.assertThat(default_quotas.items(),
                        matchers.ContainsAll(update_kwargs.items()))
