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
from tempest import test


CONF = config.CONF


class VolumesCloneTest(base.BaseVolumeTest):

    @classmethod
    def skip_checks(cls):
        super(VolumesCloneTest, cls).skip_checks()
        if not CONF.volume_feature_enabled.clone:
            raise cls.skipException("Cinder volume clones are disabled")

    @test.idempotent_id('9adae371-a257-43a5-9555-dc7c88e66e0e')
    def test_create_from_volume(self):
        # Creates a volume from another volume passing a size different from
        # the source volume.
        src_size = CONF.volume.volume_size

        src_vol = self.create_volume(size=src_size)
        # Destination volume bigger than source
        dst_vol = self.create_volume(source_volid=src_vol['id'],
                                     size=src_size + 1)

        volume = self.volumes_client.show_volume(dst_vol['id'])['volume']
        # Should allow
        self.assertEqual(volume['source_volid'], src_vol['id'])
        self.assertEqual(int(volume['size']), src_size + 1)


class VolumesV1CloneTest(VolumesCloneTest):
    _api_version = 1
