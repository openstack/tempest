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
from tempest.test import attr


class BasicOperationsImagesTest(base.BaseV2ImageTest):
    """
    Here we test the basic operations of images
    """

    @attr(type='gate')
    def test_register_upload_get_image_file(self):

        """
        Here we test these functionalities - Register image,
        upload the image file, get image and get image file api's
        """

        image_name = data_utils.rand_name('image')
        resp, body = self.create_image(name=image_name,
                                       container_format='bare',
                                       disk_format='raw',
                                       visibility='public')
        self.assertIn('id', body)
        image_id = body.get('id')
        self.assertIn('name', body)
        self.assertEqual(image_name, body['name'])
        self.assertIn('visibility', body)
        self.assertEqual('public', body['visibility'])
        self.assertIn('status', body)
        self.assertEqual('queued', body['status'])

        # Now try uploading an image file
        file_content = '*' * 1024
        image_file = StringIO.StringIO(file_content)
        resp, body = self.client.store_image(image_id, image_file)
        self.assertEqual(resp.status, 204)

        # Now try to get image details
        resp, body = self.client.get_image(image_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(image_id, body['id'])
        self.assertEqual(image_name, body['name'])
        self.assertIn('size', body)
        self.assertEqual(1024, body.get('size'))

        # Now try get image file
        resp, body = self.client.get_image_file(image_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(file_content, body)

    @attr(type='gate')
    def test_delete_image(self):
        # Deletes a image by image_id

        # Create image
        image_name = data_utils.rand_name('image')
        resp, body = self.client.create_image(name=image_name,
                                              container_format='bare',
                                              disk_format='raw',
                                              visibility='public')
        self.assertEqual(201, resp.status)
        image_id = body['id']

        # Delete Image
        self.client.delete_image(image_id)
        self.client.wait_for_resource_deletion(image_id)

        # Verifying deletion
        resp, images = self.client.image_list()
        self.assertEqual(resp.status, 200)
        self.assertNotIn(image_id, images)


class ListImagesTest(base.BaseV2ImageTest):
    """
    Here we test the listing of image information
    """

    @classmethod
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
        image_file = StringIO.StringIO('*' * random.randint(1024, 4096))
        name = data_utils.rand_name('image-')
        resp, body = cls.create_image(name=name,
                                      container_format=container_format,
                                      disk_format=disk_format,
                                      visibility='public')
        image_id = body['id']
        resp, body = cls.client.store_image(image_id, data=image_file)

        return image_id

    def _list_by_param_value_and_assert(self, params):
        """
        Perform list action with given params and validates result.
        """
        resp, images_list = self.client.image_list(params=params)
        self.assertEqual(200, resp.status)
        # Validating params of fetched images
        for image in images_list:
            for key in params:
                msg = "Failed to list images by %s" % key
                self.assertEqual(params[key], image[key], msg)

    @attr(type='gate')
    def test_index_no_params(self):
        # Simple test to see all fixture images returned
        resp, images_list = self.client.image_list()
        self.assertEqual(resp['status'], '200')
        image_list = map(lambda x: x['id'], images_list)

        for image in self.created_images:
            self.assertIn(image, image_list)

    @attr(type='gate')
    def test_list_images_param_container_format(self):
        # Test to get all images with container_format='bare'
        params = {"container_format": "bare"}
        self._list_by_param_value_and_assert(params)

    @attr(type='gate')
    def test_list_images_param_disk_format(self):
        # Test to get all images with disk_format = raw
        params = {"disk_format": "raw"}
        self._list_by_param_value_and_assert(params)

    @attr(type='gate')
    def test_list_images_param_visibility(self):
        # Test to get all images with visibility = public
        params = {"visibility": "public"}
        self._list_by_param_value_and_assert(params)

    @attr(type='gate')
    def test_list_images_param_size(self):
        # Test to get all images by size
        image_id = self.created_images[1]
        # Get image metadata
        resp, image = self.client.get_image(image_id)
        self.assertEqual(resp['status'], '200')

        params = {"size": image['size']}
        self._list_by_param_value_and_assert(params)

    @attr(type='gate')
    def test_list_images_param_min_max_size(self):
        # Test to get all images with size between 2000 to 3000
        image_id = self.created_images[1]
        # Get image metadata
        resp, image = self.client.get_image(image_id)
        self.assertEqual(resp['status'], '200')

        size = image['size']
        params = {"size_min": size - 500, "size_max": size + 500}
        resp, images_list = self.client.image_list(params=params)
        self.assertEqual(resp['status'], '200')
        image_size_list = map(lambda x: x['size'], images_list)

        for image_size in image_size_list:
            self.assertTrue(image_size >= params['size_min'] and
                            image_size <= params['size_max'],
                            "Failed to get images by size_min and size_max")

    @attr(type='gate')
    def test_list_images_param_status(self):
        # Test to get all available images
        params = {"status": "available"}
        self._list_by_param_value_and_assert(params)

    @attr(type='gate')
    def test_list_images_param_limit(self):
        # Test to get images by limit
        params = {"limit": 2}
        resp, images_list = self.client.image_list(params=params)
        self.assertEqual(resp['status'], '200')

        self.assertEqual(len(images_list), params['limit'],
                         "Failed to get images by limit")
