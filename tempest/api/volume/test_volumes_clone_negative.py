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
from tempest.lib import exceptions

CONF = config.CONF


class VolumesCloneNegativeTest(base.BaseVolumeTest):
    """Negative tests of volume clone"""

    @classmethod
    def skip_checks(cls):
        super(VolumesCloneNegativeTest, cls).skip_checks()
        if not CONF.volume_feature_enabled.clone:
            raise cls.skipException("Cinder volume clones are disabled")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9adae371-a257-43a5-459a-dc7c88e66e0e')
    def test_create_from_volume_decreasing_size(self):
        """Test cloning a volume with decreasing size will fail"""
        # Creates a volume from another volume passing a size different from
        # the source volume.
        src_size = CONF.volume.volume_size + CONF.volume.volume_size_extend
        src_vol = self.create_volume(size=src_size)

        # Destination volume smaller than source
        self.assertRaises(exceptions.BadRequest,
                          self.volumes_client.create_volume,
                          size=src_size - CONF.volume.volume_size_extend,
                          source_volid=src_vol['id'])
