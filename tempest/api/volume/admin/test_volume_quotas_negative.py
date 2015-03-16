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

from tempest_lib import exceptions as lib_exc

from tempest.api.volume import base
from tempest import test


class BaseVolumeQuotasNegativeV2TestJSON(base.BaseVolumeAdminTest):
    force_tenant_isolation = True

    @classmethod
    def setup_credentials(cls):
        super(BaseVolumeQuotasNegativeV2TestJSON, cls).setup_credentials()
        cls.demo_user = cls.isolated_creds.get_primary_creds()
        cls.demo_tenant_id = cls.demo_user.tenant_id

    @classmethod
    def resource_setup(cls):
        super(BaseVolumeQuotasNegativeV2TestJSON, cls).resource_setup()
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
        cls.snapshot = cls.create_snapshot(cls.volume['id'])

    @test.attr(type='negative')
    @test.idempotent_id('bf544854-d62a-47f2-a681-90f7a47d86b6')
    def test_quota_volumes(self):
        self.assertRaises(lib_exc.OverLimit,
                          self.volumes_client.create_volume)

    @test.attr(type='negative')
    @test.idempotent_id('02bbf63f-6c05-4357-9d98-2926a94064ff')
    def test_quota_volume_snapshots(self):
        self.assertRaises(lib_exc.OverLimit,
                          self.snapshots_client.create_snapshot,
                          self.volume['id'])

    @test.attr(type='negative')
    @test.idempotent_id('2dc27eee-8659-4298-b900-169d71a91374')
    def test_quota_volume_gigabytes(self):
        # NOTE(gfidente): quota set needs to be changed for this test
        # or we may be limited by the volumes or snaps quota number, not by
        # actual gigs usage; next line ensures shared set is restored.
        self.addCleanup(self.quotas_client.update_quota_set,
                        self.demo_tenant_id,
                        **self.shared_quota_set)

        new_quota_set = {'gigabytes': 2 * self.default_volume_size,
                         'volumes': 2, 'snapshots': 1}
        self.quotas_client.update_quota_set(
            self.demo_tenant_id,
            **new_quota_set)
        self.assertRaises(lib_exc.OverLimit,
                          self.volumes_client.create_volume)

        new_quota_set = {'gigabytes': 2 * self.default_volume_size,
                         'volumes': 1, 'snapshots': 2}
        self.quotas_client.update_quota_set(
            self.demo_tenant_id,
            **self.shared_quota_set)
        self.assertRaises(lib_exc.OverLimit,
                          self.snapshots_client.create_snapshot,
                          self.volume['id'])


class VolumeQuotasNegativeV1TestJSON(BaseVolumeQuotasNegativeV2TestJSON):
    _api_version = 1
