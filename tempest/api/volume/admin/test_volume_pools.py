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


class VolumePoolsAdminTestsJSON(base.BaseVolumeAdminTest):
    """Test getting volume pools by admin users"""

    def _assert_pools(self, with_detail=False):
        cinder_pools = self.admin_scheduler_stats_client.list_pools(
            detail=with_detail)['pools']
        self.assertNotEmpty(cinder_pools, "no cinder pools listed.")
        self.assertIn('name', cinder_pools[0])
        if with_detail:
            self.assertIn(CONF.volume.vendor_name,
                          [pool['capabilities']['vendor_name']
                           for pool in cinder_pools])

    @decorators.idempotent_id('0248a46c-e226-4933-be10-ad6fca8227e7')
    def test_get_pools_without_details(self):
        """Test getting volume pools without detail"""
        self._assert_pools()

    @decorators.idempotent_id('d4bb61f7-762d-4437-b8a4-5785759a0ced')
    def test_get_pools_with_details(self):
        """Test getting volume pools with detail"""
        self._assert_pools(with_detail=True)
