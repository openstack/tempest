# Copyright 2016 NEC Corporation.  All rights reserved.
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

from tempest.api.compute.volumes import test_attach_volume
from tempest import config
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class AttachVolumeNegativeTest(test_attach_volume.BaseAttachVolumeTest):
    """Negative tests of volume attaching"""

    @decorators.attr(type=['negative'])
    @decorators.related_bug('1630783', status_code=500)
    @decorators.idempotent_id('a313b5cd-fbd0-49cc-94de-870e99f763c7')
    def test_delete_attached_volume(self):
        """Test deleting attachemd volume should fail"""
        server, validation_resources = self._create_server()
        volume = self.create_volume()
        self.attach_volume(server, volume)

        self.assertRaises(lib_exc.BadRequest,
                          self.delete_volume, volume['id'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('aab919e2-d992-4cbb-a4ed-745c2475398c')
    def test_attach_attached_volume_to_same_server(self):
        """Test attaching attached volume to same server should fail

        Test attaching the same volume to the same instance once
        it's already attached. The nova/cinder validation for this differs
        depending on whether or not cinder v3.27 is being used to attach
        the volume to the instance.
        """
        server, validation_resources = self._create_server()
        volume = self.create_volume()

        self.attach_volume(server, volume)

        self.assertRaises(lib_exc.BadRequest,
                          self.attach_volume, server, volume)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('ee37a796-2afb-11e7-bc0f-fa163e65f5ce')
    def test_attach_attached_volume_to_different_server(self):
        """Test attaching attached volume to different server should fail"""
        server1, validation_resources = self._create_server()
        volume = self.create_volume()

        self.attach_volume(server1, volume)

        # Create server2 and attach in-use volume
        server2, validation_resources = self._create_server()
        self.assertRaises(lib_exc.BadRequest,
                          self.attach_volume, server2, volume)
