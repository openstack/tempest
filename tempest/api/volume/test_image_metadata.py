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
from tempest.common import utils
from tempest import config
from tempest.lib import decorators

CONF = config.CONF


class VolumesImageMetadata(base.BaseVolumeTest):
    """Test volume image metadata"""

    @classmethod
    def skip_checks(cls):
        super(VolumesImageMetadata, cls).skip_checks()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as Glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def resource_setup(cls):
        super(VolumesImageMetadata, cls).resource_setup()
        # Create a volume from image ID
        cls.volume = cls.create_volume(imageRef=CONF.compute.image_ref)

    @decorators.idempotent_id('03efff0b-5c75-4822-8f10-8789ac15b13e')
    @utils.services('image')
    def test_update_show_delete_image_metadata(self):
        """Test update/show/delete volume's image metadata"""
        # Update image metadata
        image_metadata = {'image_id': '5137a025-3c5f-43c1-bc64-5f41270040a5',
                          'image_name': 'image',
                          'kernel_id': '6ff710d2-942b-4d6b-9168-8c9cc2404ab1',
                          'ramdisk_id': 'somedisk'}
        self.volumes_client.update_volume_image_metadata(self.volume['id'],
                                                         **image_metadata)

        # Fetch volume's image metadata by show_volume method
        volume_image_metadata = self.volumes_client.show_volume(
            self.volume['id'])['volume']['volume_image_metadata']

        # Verify image metadata was updated
        self.assertThat(volume_image_metadata.items(),
                        matchers.ContainsAll(image_metadata.items()))

        # Delete one item from image metadata of the volume
        self.volumes_client.delete_volume_image_metadata(self.volume['id'],
                                                         'ramdisk_id')
        del image_metadata['ramdisk_id']

        # Fetch volume's image metadata by show_volume_image_metadata method
        volume_image_metadata = self.volumes_client.show_volume_image_metadata(
            self.volume['id'])['metadata']

        # Verify image metadata was updated after item deletion
        self.assertThat(volume_image_metadata.items(),
                        matchers.ContainsAll(image_metadata.items()))
        self.assertNotIn('ramdisk_id', volume_image_metadata)
