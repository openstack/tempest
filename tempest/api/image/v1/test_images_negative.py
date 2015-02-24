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

from tempest_lib import exceptions as lib_exc

from tempest.api.image import base
from tempest import test


class CreateDeleteImagesNegativeTest(base.BaseV1ImageTest):
    """Here are negative tests for the deletion and creation of images."""

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('036ede36-6160-4463-8c01-c781eee6369d')
    def test_register_with_invalid_container_format(self):
        # Negative tests for invalid data supplied to POST /images
        self.assertRaises(lib_exc.BadRequest, self.client.create_image,
                          'test', 'wrong', 'vhd')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('993face5-921d-4e84-aabf-c1bba4234a67')
    def test_register_with_invalid_disk_format(self):
        self.assertRaises(lib_exc.BadRequest, self.client.create_image,
                          'test', 'bare', 'wrong')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('bb016f15-0820-4f27-a92d-09b2f67d2488')
    def test_delete_image_with_invalid_image_id(self):
        # An image should not be deleted with invalid image id
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          '!@$%^&*()')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ec652588-7e3c-4b67-a2f2-0fa96f57c8fc')
    def test_delete_non_existent_image(self):
        # Return an error while trying to delete a non-existent image

        non_existent_image_id = '11a22b9-12a9-5555-cc11-00ab112223fa'
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          non_existent_image_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('04f72aa3-fcec-45a3-81a3-308ef7cc82bc')
    def test_delete_image_blank_id(self):
        # Return an error while trying to delete an image with blank Id
        self.assertRaises(lib_exc.NotFound, self.client.delete_image, '')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('950e5054-a3c7-4dee-ada5-e576f1087abd')
    def test_delete_image_non_hex_string_id(self):
        # Return an error while trying to delete an image with non hex id
        image_id = '11a22b9-120q-5555-cc11-00ab112223gj'
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          image_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('4ed757cd-450c-44b1-9fd1-c819748c650d')
    def test_delete_image_negative_image_id(self):
        # Return an error while trying to delete an image with negative id
        self.assertRaises(lib_exc.NotFound, self.client.delete_image, -1)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('a4a448ab-3db2-4d2d-b9b2-6a1271241dfe')
    def test_delete_image_id_is_over_35_character_limit(self):
        # Return an error while trying to delete image with id over limit
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          '11a22b9-12a9-5555-cc11-00ab112223fa-3fac')
