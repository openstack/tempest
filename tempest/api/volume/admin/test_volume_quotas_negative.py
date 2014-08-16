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
from tempest import exceptions
from tempest import test


class VolumeQuotasNegativeTestJSON(base.BaseVolumeV1AdminTest):
    _interface = "json"
    force_tenant_isolation = True

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(VolumeQuotasNegativeTestJSON, cls).setUpClass()
        demo_user = cls.isolated_creds.get_primary_creds()
        cls.demo_tenant_id = demo_user.tenant_id
        cls.shared_quota_set = {'gigabytes': 3, 'volumes': 1, 'snapshots': 1}

        # NOTE(gfidente): no need to restore original quota set
        # after the tests as they only work with tenant isolation.
        _, quota_set = cls.quotas_client.update_quota_set(
            cls.demo_tenant_id,
            **cls.shared_quota_set)

        # NOTE(gfidente): no need to delete in tearDown as
        # they are created using utility wrapper methods.
        cls.volume = cls.create_volume()
        cls.snapshot = cls.create_snapshot(cls.volume['id'])

    @test.attr(type='negative')
    def test_quota_volumes(self):
        self.assertRaises(exceptions.OverLimit,
                          self.volumes_client.create_volume,
                          size=1)

    @test.attr(type='negative')
    def test_quota_volume_snapshots(self):
        self.assertRaises(exceptions.OverLimit,
                          self.snapshots_client.create_snapshot,
                          self.volume['id'])

    @test.attr(type='negative')
    def test_quota_volume_gigabytes(self):
        # NOTE(gfidente): quota set needs to be changed for this test
        # or we may be limited by the volumes or snaps quota number, not by
        # actual gigs usage; next line ensures shared set is restored.
        self.addCleanup(self.quotas_client.update_quota_set,
                        self.demo_tenant_id,
                        **self.shared_quota_set)

        new_quota_set = {'gigabytes': 2, 'volumes': 2, 'snapshots': 1}
        _, quota_set = self.quotas_client.update_quota_set(
            self.demo_tenant_id,
            **new_quota_set)
        self.assertRaises(exceptions.OverLimit,
                          self.volumes_client.create_volume,
                          size=1)

        new_quota_set = {'gigabytes': 2, 'volumes': 1, 'snapshots': 2}
        _, quota_set = self.quotas_client.update_quota_set(
            self.demo_tenant_id,
            **self.shared_quota_set)
        self.assertRaises(exceptions.OverLimit,
                          self.snapshots_client.create_snapshot,
                          self.volume['id'])


class VolumeQuotasNegativeTestXML(VolumeQuotasNegativeTestJSON):
    _interface = "xml"
