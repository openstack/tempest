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
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF


class VolumeSnapshotQuotasNegativeV2TestJSON(base.BaseVolumeAdminTest):
    force_tenant_isolation = True

    @classmethod
    def skip_checks(cls):
        super(VolumeSnapshotQuotasNegativeV2TestJSON, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException('Cinder volume snapshots are disabled')

    @classmethod
    def setup_credentials(cls):
        super(VolumeSnapshotQuotasNegativeV2TestJSON, cls).setup_credentials()
        cls.demo_tenant_id = cls.os.credentials.tenant_id

    @classmethod
    def resource_setup(cls):
        super(VolumeSnapshotQuotasNegativeV2TestJSON, cls).resource_setup()
        cls.default_volume_size = cls.volumes_client.default_volume_size
        cls.shared_quota_set = {'gigabytes': 3 * cls.default_volume_size,
                                'volumes': 1, 'snapshots': 1}

        # NOTE(gfidente): no need to restore original quota set
        # after the tests as they only work with tenant isolation.
        cls.quotas_client.update_quota_set(
            cls.demo_tenant_id,
            **cls.shared_quota_set)

        # NOTE(gfidente): no need to delete in tearDown as
        # they are created using utility wrapper methods.
        cls.volume = cls.create_volume()
        cls.snapshot = cls.create_snapshot(volume_id=cls.volume['id'])

    @test.attr(type='negative')
    @test.idempotent_id('02bbf63f-6c05-4357-9d98-2926a94064ff')
    def test_quota_volume_snapshots(self):
        self.assertRaises(lib_exc.OverLimit,
                          self.snapshots_client.create_snapshot,
                          volume_id=self.volume['id'])

    @test.attr(type='negative')
    @test.idempotent_id('c99a1ca9-6cdf-498d-9fdf-25832babef27')
    def test_quota_volume_gigabytes_snapshots(self):
        self.addCleanup(self.quotas_client.update_quota_set,
                        self.demo_tenant_id,
                        **self.shared_quota_set)
        new_quota_set = {'gigabytes': 2 * self.default_volume_size,
                         'volumes': 1, 'snapshots': 2}
        self.quotas_client.update_quota_set(
            self.demo_tenant_id,
            **new_quota_set)
        self.assertRaises(lib_exc.OverLimit,
                          self.snapshots_client.create_snapshot,
                          volume_id=self.volume['id'])


class VolumeSnapshotNegativeV1TestJSON(VolumeSnapshotQuotasNegativeV2TestJSON):
    _api_version = 1
