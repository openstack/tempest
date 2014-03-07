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

import uuid

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class VolumesSnapshotNegativeTest(base.BaseVolumeV1Test):
    _interface = "json"

    @test.attr(type=['negative', 'gate'])
    def test_create_snapshot_with_nonexistent_volume_id(self):
        # Create a snapshot with nonexistent volume id
        s_name = data_utils.rand_name('snap')
        self.assertRaises(exceptions.NotFound,
                          self.snapshots_client.create_snapshot,
                          str(uuid.uuid4()), display_name=s_name)

    @test.attr(type=['negative', 'gate'])
    def test_create_snapshot_without_passing_volume_id(self):
        # Create a snapshot without passing volume id
        s_name = data_utils.rand_name('snap')
        self.assertRaises(exceptions.NotFound,
                          self.snapshots_client.create_snapshot,
                          None, display_name=s_name)


class VolumesSnapshotNegativeTestXML(VolumesSnapshotNegativeTest):
    _interface = "xml"
