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
from tempest.common import utils
from tempest import config
from tempest.lib import decorators


CONF = config.CONF


class VolumesCloneTest(base.BaseVolumeTest):
    """Test volume clone"""

    @classmethod
    def skip_checks(cls):
        super(VolumesCloneTest, cls).skip_checks()
        if not CONF.volume_feature_enabled.clone:
            raise cls.skipException("Cinder volume clones are disabled")

    def _verify_volume_clone(self, source_volume, cloned_volume,
                             bootable='false', extra_size=0):

        cloned_vol_details = self.volumes_client.show_volume(
            cloned_volume['id'])['volume']

        self.assertEqual(source_volume['id'],
                         cloned_vol_details['source_volid'])
        self.assertEqual(source_volume['size'] + extra_size,
                         cloned_vol_details['size'])
        self.assertEqual(bootable, cloned_vol_details['bootable'])

    @decorators.idempotent_id('9adae371-a257-43a5-9555-dc7c88e66e0e')
    def test_create_from_volume(self):
        """Test cloning a volume with increasing size"""
        # Creates a volume from another volume passing a size different from
        # the source volume.
        src_size = CONF.volume.volume_size

        src_vol = self.create_volume(size=src_size)
        # Destination volume bigger than source
        dst_vol = self.create_volume(source_volid=src_vol['id'],
                                     size=src_size + 1)

        self._verify_volume_clone(src_vol, dst_vol, extra_size=1)

    @decorators.idempotent_id('cbbcd7c6-5a6c-481a-97ac-ca55ab715d16')
    @utils.services('image')
    def test_create_from_bootable_volume(self):
        """Test cloning a bootable volume"""
        # Create volume from image
        img_uuid = CONF.compute.image_ref
        src_vol = self.create_volume(imageRef=img_uuid)

        # Create a volume from the bootable volume
        cloned_vol = self.create_volume(source_volid=src_vol['id'])

        self._verify_volume_clone(src_vol, cloned_vol, bootable='true')
