# Copyright 2016 OpenStack Foundation
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

from tempest.api.volume import base
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


# NOTE(zhufl): This inherits from BaseVolumeAdminTest because
# it requires force_tenant_isolation=True, which need admin
# credentials to create non-admin users for the tests.
class AbsoluteLimitsTests(base.BaseVolumeAdminTest):  # noqa

    # avoid existing volumes of pre-defined tenant
    force_tenant_isolation = True

    @classmethod
    def resource_setup(cls):
        super(AbsoluteLimitsTests, cls).resource_setup()

        # Create a shared volume for tests
        cls.volume = cls.create_volume()

    @classmethod
    def skip_checks(cls):
        super(AbsoluteLimitsTests, cls).skip_checks()
        if not CONF.auth.use_dynamic_credentials:
            raise cls.skipException("Must use dynamic credentials.")

    @decorators.idempotent_id('8e943f53-e9d6-4272-b2e9-adcf2f7c29ad')
    def test_get_volume_absolute_limits(self):
        # get volume limit for a tenant
        absolute_limits = \
            self.volume_limits_client.show_limits(
            )['limits']['absolute']

        # verify volume limits and defaults per tenants
        self.assertEqual(absolute_limits['totalGigabytesUsed'],
                         CONF.volume.volume_size)
        self.assertEqual(absolute_limits['totalVolumesUsed'], 1)
        self.assertEqual(absolute_limits['totalSnapshotsUsed'], 0)
        self.assertEqual(absolute_limits['totalBackupsUsed'], 0)
        self.assertEqual(absolute_limits['totalBackupGigabytesUsed'], 0)
