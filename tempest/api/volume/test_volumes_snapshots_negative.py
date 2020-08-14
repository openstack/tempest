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
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class VolumesSnapshotNegativeTestJSON(base.BaseVolumeTest):
    """Negative tests of volume snapshot"""

    @classmethod
    def skip_checks(cls):
        super(VolumesSnapshotNegativeTestJSON, cls).skip_checks()
        if not CONF.volume_feature_enabled.snapshot:
            raise cls.skipException("Cinder volume snapshots are disabled")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('e3e466af-70ab-4f4b-a967-ab04e3532ea7')
    def test_create_snapshot_with_nonexistent_volume_id(self):
        """Test creating snapshot from non existent volume should fail"""
        s_name = data_utils.rand_name(self.__class__.__name__ + '-snap')
        self.assertRaises(lib_exc.NotFound,
                          self.snapshots_client.create_snapshot,
                          volume_id=data_utils.rand_uuid(),
                          display_name=s_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('bb9da53e-d335-4309-9c15-7e76fd5e4d6d')
    def test_create_snapshot_without_passing_volume_id(self):
        """Test creating snapshot without passing volume_id should fail"""
        # Create a snapshot without passing volume id
        s_name = data_utils.rand_name(self.__class__.__name__ + '-snap')
        self.assertRaises(lib_exc.NotFound,
                          self.snapshots_client.create_snapshot,
                          volume_id=None, display_name=s_name)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('677863d1-34f9-456d-b6ac-9924f667a7f4')
    def test_volume_from_snapshot_decreasing_size(self):
        """Test creating volume from snapshot with decreasing size

        creating volume from snapshot with decreasing size should fail.
        """
        # Creates a volume a snapshot passing a size different from the source
        src_size = CONF.volume.volume_size * 2

        src_vol = self.create_volume(size=src_size)
        src_snap = self.create_snapshot(src_vol['id'])

        # Destination volume smaller than source
        self.assertRaises(lib_exc.BadRequest,
                          self.volumes_client.create_volume,
                          size=CONF.volume.volume_size,
                          snapshot_id=src_snap['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8fd92339-e22f-4591-86b4-1e2215372a40')
    def test_list_snapshot_invalid_param_limit(self):
        """Test listing snapshots with invalid limit param should fail"""
        self.assertRaises(lib_exc.BadRequest,
                          self.snapshots_client.list_snapshots,
                          limit='invalid')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('27b5f37f-bf69-4e8c-986e-c44f3d6819b8')
    def test_list_snapshots_invalid_param_sort(self):
        """Test listing snapshots with invalid sort key should fail"""
        self.assertRaises(lib_exc.BadRequest,
                          self.snapshots_client.list_snapshots,
                          sort_key='invalid')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b68deeda-ca79-4a32-81af-5c51179e553a')
    def test_list_snapshots_invalid_param_marker(self):
        """Test listing snapshots with invalid marker should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.snapshots_client.list_snapshots,
                          marker=data_utils.rand_uuid())
