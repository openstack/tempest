# Copyright 2012 OpenStack Foundation
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

import testtools

from tempest.api.volume import base
from tempest.common import waiters
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class VolumesExtendTest(base.BaseVolumeTest):

    @decorators.idempotent_id('9a36df71-a257-43a5-9555-dc7c88e66e0e')
    def test_volume_extend(self):
        # Extend Volume Test.
        volume = self.create_volume()
        extend_size = volume['size'] + 1
        self.volumes_client.extend_volume(volume['id'],
                                          new_size=extend_size)
        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        volume = self.volumes_client.show_volume(volume['id'])['volume']
        self.assertEqual(volume['size'], extend_size)

    @decorators.idempotent_id('86be1cba-2640-11e5-9c82-635fb964c912')
    @testtools.skipUnless(CONF.volume_feature_enabled.snapshot,
                          "Cinder volume snapshots are disabled")
    @decorators.skip_because(bug='1687044')
    def test_volume_extend_when_volume_has_snapshot(self):
        volume = self.create_volume()
        self.create_snapshot(volume['id'])

        extend_size = volume['size'] + 1
        self.volumes_client.extend_volume(volume['id'], new_size=extend_size)

        waiters.wait_for_volume_resource_status(self.volumes_client,
                                                volume['id'], 'available')
        resized_volume = self.volumes_client.show_volume(
            volume['id'])['volume']
        self.assertEqual(extend_size, resized_volume['size'])
