# Copyright 2014 OpenStack Foundation
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
from tempest.lib import exceptions as lib_exc

CONF = config.CONF
QUOTA_KEYS = ['gigabytes', 'snapshots', 'volumes', 'backups',
              'backup_gigabytes', 'per_volume_gigabytes']


class VolumeSnapshotQuotasNegativeTestJSON(base.BaseVolumeAdminTest):
    """Negative tests of volume snapshot quotas"""

    @classmethod
    def skip_checks(cls):
        super(VolumeSnapshotQuotasNegativeTestJSON, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException('Cinder volume snapshots are disabled')

    @classmethod
    def setup_credentials(cls):
        super(VolumeSnapshotQuotasNegativeTestJSON, cls).setup_credentials()
        cls.demo_tenant_id = cls.os_primary.credentials.tenant_id

    @classmethod
    def resource_setup(cls):
        super(VolumeSnapshotQuotasNegativeTestJSON, cls).resource_setup()

        # Save the current set of quotas, then set up the cleanup method
        # to restore the quotas to their original values after the tests
        # from this class are done. This is needed just in case Tempest is
        # configured to use pre-provisioned projects/user accounts.
        original_quota_set = (cls.admin_quotas_client.show_quota_set(
            cls.demo_tenant_id)['quota_set'])
        cleanup_quota_set = dict(
            (k, v) for k, v in original_quota_set.items() if k in QUOTA_KEYS)
        cls.addClassResourceCleanup(cls.admin_quotas_client.update_quota_set,
                                    cls.demo_tenant_id, **cleanup_quota_set)

        cls.default_volume_size = CONF.volume.volume_size
        cls.shared_quota_set = {'gigabytes': 3 * cls.default_volume_size,
                                'volumes': 1, 'snapshots': 1}

        cls.admin_quotas_client.update_quota_set(
            cls.demo_tenant_id,
            **cls.shared_quota_set)

        # NOTE(gfidente): no need to delete in tearDown as
        # they are created using utility wrapper methods.
        cls.volume = cls.create_volume()
        cls.snapshot = cls.create_snapshot(volume_id=cls.volume['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('02bbf63f-6c05-4357-9d98-2926a94064ff')
    def test_quota_volume_snapshots(self):
        """Test creating snapshot exceeding snapshots quota should fail"""
        self.assertRaises(lib_exc.OverLimit,
                          self.snapshots_client.create_snapshot,
                          volume_id=self.volume['id'])

    @decorators.attr(type='negative')
    @decorators.idempotent_id('c99a1ca9-6cdf-498d-9fdf-25832babef27')
    def test_quota_volume_gigabytes_snapshots(self):
        """Test creating snapshot exceeding gigabytes quota should fail"""
        self.addCleanup(self.admin_quotas_client.update_quota_set,
                        self.demo_tenant_id,
                        **self.shared_quota_set)
        new_quota_set = {'gigabytes': 2 * self.default_volume_size,
                         'volumes': 1, 'snapshots': 2}
        self.admin_quotas_client.update_quota_set(
            self.demo_tenant_id,
            **new_quota_set)
        self.assertRaises(lib_exc.OverLimit,
                          self.snapshots_client.create_snapshot,
                          volume_id=self.volume['id'])
