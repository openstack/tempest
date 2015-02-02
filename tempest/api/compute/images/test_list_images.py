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

from tempest.api.compute import base
from tempest import config
from tempest import test

CONF = config.CONF


class ListImagesTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def resource_setup(cls):
        super(ListImagesTestJSON, cls).resource_setup()
        if not CONF.service_available.glance:
            skip_msg = ("%s skipped as glance is not available" % cls.__name__)
            raise cls.skipException(skip_msg)
        cls.client = cls.images_client

    @test.attr(type='smoke')
    def test_get_image(self):
        # Returns the correct details for a single image
        image = self.client.get_image(self.image_ref)
        self.assertEqual(self.image_ref, image['id'])

    @test.attr(type='smoke')
    def test_list_images(self):
        # The list of all images should contain the image
        images = self.client.list_images()
        found = any([i for i in images if i['id'] == self.image_ref])
        self.assertTrue(found)

    @test.attr(type='smoke')
    def test_list_images_with_detail(self):
        # Detailed list of all images should contain the expected images
        images = self.client.list_images_with_detail()
        found = any([i for i in images if i['id'] == self.image_ref])
        self.assertTrue(found)
