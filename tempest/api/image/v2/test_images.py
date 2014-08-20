# Copyright 2013 OpenStack Foundation
# Copyright 2013 IBM Corp
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

import cStringIO as StringIO
import random

from tempest.api.image import base
from tempest.common.utils import data_utils
from tempest import test


class BasicOperationsImagesTest(base.BaseV2ImageTest):
    """
    Here we test the basic operations of images
    """

    @test.attr(type='gate')
    def test_register_upload_get_image_file(self):

        """
        Here we test these functionalities - Register image,
        upload the image file, get image and get image file api's
        """

        uuid = '00000000-1111-2222-3333-444455556666'
        image_name = data_utils.rand_name('image')
        _, body = self.create_image(name=image_name,
                                    container_format='bare',
                                    disk_format='raw',
                                    visibility='private',
                                    ramdisk_id=uuid)
        self.assertIn('id', body)
        image_id = body.get('id')
        self.assertIn('name', body)
        self.assertEqual(image_name, body['name'])
        self.assertIn('visibility', body)
        self.assertEqual('private', body['visibility'])
        self.assertIn('status', body)
        self.assertEqual('queued', body['status'])

        # Now try uploading an image file
        file_content = data_utils.random_bytes()
        image_file = StringIO.StringIO(file_content)
        self.client.store_image(image_id, image_file)

        # Now try to get image details
        _, body = self.client.get_image(image_id)
        self.assertEqual(image_id, body['id'])
        self.assertEqual(image_name, body['name'])
        self.assertEqual(uuid, body['ramdisk_id'])
        self.assertIn('size', body)
        self.assertEqual(1024, body.get('size'))

        # Now try get image file
        _, body = self.client.get_image_file(image_id)
        self.assertEqual(file_content, body)

    @test.attr(type='gate')
    def test_delete_image(self):
        # Deletes an image by image_id

        # Create image
        image_name = data_utils.rand_name('image')
        _, body = self.client.create_image(name=image_name,
                                           container_format='bare',
                                           disk_format='raw',
                                           visibility='private')
        image_id = body['id']

        # Delete Image
        self.client.delete_image(image_id)
        self.client.wait_for_resource_deletion(image_id)

        # Verifying deletion
        _, images = self.client.image_list()
        images_id = [item['id'] for item in images]
        self.assertNotIn(image_id, images_id)

    @test.attr(type='gate')
    def test_update_image(self):
        # Updates an image by image_id

        # Create image
        image_name = data_utils.rand_name('image')
        _, body = self.client.create_image(name=image_name,
                                           container_format='bare',
                                           disk_format='iso',
                                           visibility='private')
        self.addCleanup(self.client.delete_image, body['id'])
        self.assertEqual('queued', body['status'])
        image_id = body['id']

        # Now try uploading an image file
        image_file = StringIO.StringIO(data_utils.random_bytes())
        self.client.store_image(image_id, image_file)

        # Update Image
        new_image_name = data_utils.rand_name('new-image')
        _, body = self.client.update_image(image_id, [
            dict(replace='/name', value=new_image_name)])

        # Verifying updating

        _, body = self.client.get_image(image_id)
        self.assertEqual(image_id, body['id'])
        self.assertEqual(new_image_name, body['name'])


class ListImagesTest(base.BaseV2ImageTest):
    """
    Here we test the listing of image information
    """

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(ListImagesTest, cls).setUpClass()
        # We add a few images here to test the listing functionality of
        # the images API
        cls._create_standard_image('bare', 'raw')
        cls._create_standard_image('bare', 'raw')
        cls._create_standard_image('ami', 'raw')
        # Add some more for listing
        cls._create_standard_image('ami', 'ami')
        cls._create_standard_image('ari', 'ari')
        cls._create_standard_image('aki', 'aki')

    @classmethod
    def _create_standard_image(cls, container_format, disk_format):
        """
        Create a new standard image and return the ID of the newly-registered
        image. Note that the size of the new image is a random number between
        1024 and 4096
        """
        size = random.randint(1024, 4096)
        image_file = StringIO.StringIO(data_utils.random_bytes(size))
        name = data_utils.rand_name('image-')
        _, body = cls.create_image(name=name,
                                   container_format=container_format,
                                   disk_format=disk_format,
                                   visibility='private')
        image_id = body['id']
        cls.client.store_image(image_id, data=image_file)

        return image_id

    def _list_by_param_value_and_assert(self, params):
        """
        Perform list action with given params and validates result.
        """
        _, images_list = self.client.image_list(params=params)
        # Validating params of fetched images
        for image in images_list:
            for key in params:
                msg = "Failed to list images by %s" % key
                self.assertEqual(params[key], image[key], msg)

    @test.attr(type='gate')
    def test_index_no_params(self):
        # Simple test to see all fixture images returned
        _, images_list = self.client.image_list()
        image_list = map(lambda x: x['id'], images_list)

        for image in self.created_images:
            self.assertIn(image, image_list)

    @test.attr(type='gate')
    def test_list_images_param_name(self):
        # Test to get all images with name
        image_id = self.created_images[1]
        # Get image metadata
        _, image = self.client.get_image(image_id)

        params = {"name": image['name']}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_list_images_param_container_format(self):
        # Test to get all images with container_format='bare'
        params = {"container_format": "bare"}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_list_images_param_disk_format(self):
        # Test to get all images with disk_format = raw
        params = {"disk_format": "raw"}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_list_images_param_visibility(self):
        # Test to get all images with visibility = private
        params = {"visibility": "private"}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_list_images_param_size(self):
        # Test to get all images by size
        image_id = self.created_images[1]
        # Get image metadata
        _, image = self.client.get_image(image_id)

        params = {"size": image['size']}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_list_images_param_min_max_size(self):
        # Test to get all images with size between 2000 to 3000
        image_id = self.created_images[1]
        # Get image metadata
        _, image = self.client.get_image(image_id)

        size = image['size']
        params = {"size_min": size - 500, "size_max": size + 500}
        _, images_list = self.client.image_list(params=params)
        image_size_list = map(lambda x: x['size'], images_list)

        for image_size in image_size_list:
            self.assertTrue(image_size >= params['size_min'] and
                            image_size <= params['size_max'],
                            "Failed to get images by size_min and size_max")

    @test.attr(type='gate')
    def test_list_images_param_status(self):
        # Test to get all active images
        params = {"status": "active"}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_list_images_param_limit(self):
        # Test to get images by limit
        params = {"limit": 2}
        _, images_list = self.client.image_list(params=params)

        self.assertEqual(len(images_list), params['limit'],
                         "Failed to get images by limit")

    @test.attr(type='gate')
    def test_list_images_param_owner(self):
        # Test to get images by owner
        params = {"owner": self.client.tenant_id}
        self._list_by_param_value_and_assert(params)

    @test.attr(type='gate')
    def test_list_images_param_tag(self):
        # Test to get images by tag
        image_id = self.created_images[1]
        # Creating image tag and verify it.
        tag = data_utils.rand_name('tag-')
        self.client.add_image_tag(image_id, tag)

        params = {"tag": tag}
        _, images_list = self.client.image_list(params=params)
        image_tags_list = map(lambda x: x['tags'], images_list)

        for image_tags in image_tags_list:
            self.assertIn(tag, image_tags)

    @test.attr(type='gate')
    def test_list_images_param_marker(self):
        # Test to get images by marker
        _, images_list = self.client.image_list()
        image_id_list = map(lambda x: x['id'], images_list)
        image1_id = image_id_list[-1]
        image2_id = image_id_list[-2]
        image3_id = image_id_list[-3]

        params = {"marker": image2_id}
        _, images_list = self.client.image_list(params=params)
        image_id_list = map(lambda x: x['id'], images_list)

        self.assertIn(image1_id, image_id_list)
        self.assertNotIn(image2_id, image_id_list)
        self.assertNotIn(image3_id, image_id_list)

    @test.attr(type='gate')
    def test_get_image_schema(self):
        # Test to get image schema
        schema = "image"
        _, body = self.client.get_schema(schema)
        self.assertEqual("image", body['name'])

    @test.attr(type='gate')
    def test_get_images_schema(self):
        # Test to get images schema
        schema = "images"
        _, body = self.client.get_schema(schema)
        self.assertEqual("images", body['name'])
