# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
# Copyright 2013 IBM Corp.
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

import uuid

from tempest_lib import exceptions as lib_exc

from tempest.api.image import base
from tempest import test


class ImagesNegativeTest(base.BaseV2ImageTest):

    """
    here we have -ve tests for get_image and delete_image api

    Tests
        ** get non-existent image
        ** get image with image_id=NULL
        ** get the deleted image
        ** delete non-existent image
        ** delete rimage with  image_id=NULL
        ** delete the deleted image
     """

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('668743d5-08ad-4480-b2b8-15da34f81d9f')
    def test_get_non_existent_image(self):
        # get the non-existent image
        non_existent_id = str(uuid.uuid4())
        self.assertRaises(lib_exc.NotFound, self.client.get_image,
                          non_existent_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('ef45000d-0a72-4781-866d-4cb7bf2562ad')
    def test_get_image_null_id(self):
        # get image with image_id = NULL
        image_id = ""
        self.assertRaises(lib_exc.NotFound, self.client.get_image, image_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('e57fc127-7ba0-4693-92d7-1d8a05ebcba9')
    def test_get_delete_deleted_image(self):
        # get and delete the deleted image
        # create and delete image
        body = self.client.create_image(name='test',
                                        container_format='bare',
                                        disk_format='raw')
        image_id = body['id']
        self.client.delete_image(image_id)
        self.client.wait_for_resource_deletion(image_id)

        # get the deleted image
        self.assertRaises(lib_exc.NotFound, self.client.get_image, image_id)

        # delete the deleted image
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          image_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('6fe40f1c-57bd-4918-89cc-8500f850f3de')
    def test_delete_non_existing_image(self):
        # delete non-existent image
        non_existent_image_id = str(uuid.uuid4())
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          non_existent_image_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('32248db1-ab88-4821-9604-c7c369f1f88c')
    def test_delete_image_null_id(self):
        # delete image with image_id=NULL
        image_id = ""
        self.assertRaises(lib_exc.NotFound, self.client.delete_image,
                          image_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('292bd310-369b-41c7-a7a3-10276ef76753')
    def test_register_with_invalid_container_format(self):
        # Negative tests for invalid data supplied to POST /images
        self.assertRaises(lib_exc.BadRequest, self.client.create_image,
                          'test', 'wrong', 'vhd')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('70c6040c-5a97-4111-9e13-e73665264ce1')
    def test_register_with_invalid_disk_format(self):
        self.assertRaises(lib_exc.BadRequest, self.client.create_image,
                          'test', 'bare', 'wrong')
