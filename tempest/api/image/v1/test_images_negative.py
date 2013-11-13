# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 IBM Corp.
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

from tempest.api.image import base
from tempest import exceptions
from tempest.test import attr


class CreateDeleteImagesNegativeTest(base.BaseV1ImageTest):
    """Here are negative tests for the deletion and creation of images."""

    @attr(type=['negative', 'gate'])
    def test_register_with_invalid_container_format(self):
        # Negative tests for invalid data supplied to POST /images
        self.assertRaises(exceptions.BadRequest, self.client.create_image,
                          'test', 'wrong', 'vhd')

    @attr(type=['negative', 'gate'])
    def test_register_with_invalid_disk_format(self):
        self.assertRaises(exceptions.BadRequest, self.client.create_image,
                          'test', 'bare', 'wrong')

    @attr(type=['negative', 'gate'])
    def test_delete_image_with_invalid_image_id(self):
        # An image should not be deleted with invalid image id
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          '!@$%^&*()')

    @attr(type=['negative', 'gate'])
    def test_delete_non_existent_image(self):
        # Return an error while trying to delete a non-existent image

        non_existent_image_id = '11a22b9-12a9-5555-cc11-00ab112223fa'
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          non_existent_image_id)

    @attr(type=['negative', 'gate'])
    def test_delete_image_blank_id(self):
        # Return an error while trying to delete an image with blank Id
        self.assertRaises(exceptions.NotFound, self.client.delete_image, '')

    @attr(type=['negative', 'gate'])
    def test_delete_image_non_hex_string_id(self):
        # Return an error while trying to delete an image with non hex id
        image_id = '11a22b9-120q-5555-cc11-00ab112223gj'
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          image_id)

    @attr(type=['negative', 'gate'])
    def test_delete_image_negative_image_id(self):
        # Return an error while trying to delete an image with negative id
        self.assertRaises(exceptions.NotFound, self.client.delete_image, -1)

    @attr(type=['negative', 'gate'])
    def test_delete_image_id_is_over_35_character_limit(self):
        # Return an error while trying to delete image with id over limit
        self.assertRaises(exceptions.NotFound, self.client.delete_image,
                          '11a22b9-12a9-5555-cc11-00ab112223fa-3fac')
