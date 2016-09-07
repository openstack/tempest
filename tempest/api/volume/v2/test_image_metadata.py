# Copyright 2016 Red Hat, Inc.
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

from testtools import matchers

from tempest.api.volume import base
from tempest import config
from tempest import test

CONF = config.CONF


class VolumesV2ImageMetadata(base.BaseVolumeTest):

    @classmethod
    def resource_setup(cls):
        super(VolumesV2ImageMetadata, cls).resource_setup()
        # Create a volume from image ID
        cls.volume = cls.create_volume(imageRef=CONF.compute.image_ref)

    @test.idempotent_id('03efff0b-5c75-4822-8f10-8789ac15b13e')
    @test.services('image')
    def test_update_image_metadata(self):
        # Update image metadata
        image_metadata = {'image_id': '5137a025-3c5f-43c1-bc64-5f41270040a5',
                          'image_name': 'image',
                          'kernel_id': '6ff710d2-942b-4d6b-9168-8c9cc2404ab1',
                          'ramdisk_id': 'somedisk'}
        self.volumes_client.update_volume_image_metadata(self.volume['id'],
                                                         **image_metadata)

        # Fetch image metadata from the volume
        volume_image_metadata = self.volumes_client.show_volume(
            self.volume['id'])['volume']['volume_image_metadata']

        # Verify image metadata was updated
        self.assertThat(volume_image_metadata.items(),
                        matchers.ContainsAll(image_metadata.items()))

        # Delete one item from image metadata of the volume
        self.volumes_client.delete_volume_image_metadata(self.volume['id'],
                                                         'ramdisk_id')
        del image_metadata['ramdisk_id']

        # Fetch the new image metadata from the volume
        volume_image_metadata = self.volumes_client.show_volume(
            self.volume['id'])['volume']['volume_image_metadata']

        # Verify image metadata was updated after item deletion
        self.assertThat(volume_image_metadata.items(),
                        matchers.ContainsAll(image_metadata.items()))
        self.assertNotIn('ramdisk_id', volume_image_metadata)
