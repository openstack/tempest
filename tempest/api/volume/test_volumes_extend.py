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

from tempest.api.volume import base
from tempest import config
from tempest import test

CONF = config.CONF


class VolumesV2ExtendTest(base.BaseVolumeTest):

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(VolumesV2ExtendTest, cls).setUpClass()
        cls.client = cls.volumes_client

    @test.attr(type='gate')
    def test_volume_extend(self):
        # Extend Volume Test.
        self.volume = self.create_volume()
        extend_size = int(self.volume['size']) + 1
        _, body = self.client.extend_volume(self.volume['id'], extend_size)
        self.client.wait_for_volume_status(self.volume['id'], 'available')
        _, volume = self.client.get_volume(self.volume['id'])
        self.assertEqual(int(volume['size']), extend_size)


class VolumesV2ExtendTestXML(VolumesV2ExtendTest):
    _interface = "xml"


class VolumesV1ExtendTest(VolumesV2ExtendTest):
    _api_version = 1


class VolumesV1ExtendTestXML(VolumesV1ExtendTest):
    _interface = "xml"
