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

import random

from six import moves

from oslo_log import log as logging
from tempest.api.image import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BasicOperationsImagesTest(base.BaseV2ImageTest):
    """Here we test the basic operations of images"""

    @test.attr(type='smoke')
    @test.idempotent_id('139b765e-7f3d-4b3d-8b37-3ca3876ee318')
    def test_register_upload_get_image_file(self):
        """Here we test these functionalities

        Register image, upload the image file, get image and get image
        file api's
        """

        uuid = '00000000-1111-2222-3333-444455556666'
        image_name = data_utils.rand_name('image')
        container_format = CONF.image.container_formats[0]
        disk_format = CONF.image.disk_formats[0]
        body = self.create_image(name=image_name,
                                 container_format=container_format,
                                 disk_format=disk_format,
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
        image_file = moves.cStringIO(file_content)
        self.client.store_image_file(image_id, image_file)

        # Now try to get image details
        body = self.client.show_image(image_id)
        self.assertEqual(image_id, body['id'])
        self.assertEqual(image_name, body['name'])
        self.assertEqual(uuid, body['ramdisk_id'])
        self.assertIn('size', body)
        self.assertEqual(1024, body.get('size'))

        # Now try get image file
        body = self.client.show_image_file(image_id)
        self.assertEqual(file_content, body.data)

    @test.attr(type='smoke')
    @test.idempotent_id('f848bb94-1c6e-45a4-8726-39e3a5b23535')
    def test_delete_image(self):
        # Deletes an image by image_id

        # Create image
        image_name = data_utils.rand_name('image')
        container_format = CONF.image.container_formats[0]
        disk_format = CONF.image.disk_formats[0]
        body = self.client.create_image(name=image_name,
                                        container_format=container_format,
                                        disk_format=disk_format,
                                        visibility='private')
        image_id = body['id']

        # Delete Image
        self.client.delete_image(image_id)
        self.client.wait_for_resource_deletion(image_id)

        # Verifying deletion
        images = self.client.list_images()['images']
        images_id = [item['id'] for item in images]
        self.assertNotIn(image_id, images_id)

    @test.attr(type='smoke')
    @test.idempotent_id('f66891a7-a35c-41a8-b590-a065c2a1caa6')
    def test_update_image(self):
        # Updates an image by image_id

        # Create image
        image_name = data_utils.rand_name('image')
        container_format = CONF.image.container_formats[0]
        disk_format = CONF.image.disk_formats[0]
        body = self.client.create_image(name=image_name,
                                        container_format=container_format,
                                        disk_format=disk_format,
                                        visibility='private')
        self.addCleanup(self.client.delete_image, body['id'])
        self.assertEqual('queued', body['status'])
        image_id = body['id']

        # Now try uploading an image file
        image_file = moves.cStringIO(data_utils.random_bytes())
        self.client.store_image_file(image_id, image_file)

        # Update Image
        new_image_name = data_utils.rand_name('new-image')
        body = self.client.update_image(image_id, [
            dict(replace='/name', value=new_image_name)])

        # Verifying updating

        body = self.client.show_image(image_id)
        self.assertEqual(image_id, body['id'])
        self.assertEqual(new_image_name, body['name'])


class ListImagesTest(base.BaseV2ImageTest):
    """Here we test the listing of image information"""

    @classmethod
    def resource_setup(cls):
        super(ListImagesTest, cls).resource_setup()
        # We add a few images here to test the listing functionality of
        # the images API
        container_fmts = CONF.image.container_formats
        disk_fmts = CONF.image.disk_formats
        all_pairs = [(container_fmt, disk_fmt)
                     for container_fmt in container_fmts
                     for disk_fmt in disk_fmts]

        for (container_fmt, disk_fmt) in all_pairs[:6]:
            LOG.debug("Creating an image"
                      "(Container format: %s, Disk format: %s).",
                      container_fmt, disk_fmt)
            cls._create_standard_image(container_fmt, disk_fmt)

    @classmethod
    def _create_standard_image(cls, container_format, disk_format):
        """Create a new standard image and return the newly-registered image-id

        Note that the size of the new image is a random number between
        1024 and 4096
        """
        size = random.randint(1024, 4096)
        image_file = moves.cStringIO(data_utils.random_bytes(size))
        name = data_utils.rand_name('image')
        body = cls.create_image(name=name,
                                container_format=container_format,
                                disk_format=disk_format,
                                visibility='private')
        image_id = body['id']
        cls.client.store_image_file(image_id, data=image_file)

        return image_id

    def _list_by_param_value_and_assert(self, params):
        """Perform list action with given params and validates result."""

        images_list = self.client.list_images(params=params)['images']
        # Validating params of fetched images
        for image in images_list:
            for key in params:
                msg = "Failed to list images by %s" % key
                self.assertEqual(params[key], image[key], msg)

    @test.idempotent_id('1e341d7a-90a9-494c-b143-2cdf2aeb6aee')
    def test_list_no_params(self):
        # Simple test to see all fixture images returned
        images_list = self.client.list_images()['images']
        image_list = map(lambda x: x['id'], images_list)

        for image in self.created_images:
            self.assertIn(image, image_list)

    @test.idempotent_id('9959ca1d-1aa7-4b7a-a1ea-0fff0499b37e')
    def test_list_images_param_container_format(self):
        # Test to get all images with container_format='bare'
        params = {"container_format": "bare"}
        self._list_by_param_value_and_assert(params)

    @test.idempotent_id('4a4735a7-f22f-49b6-b0d9-66e1ef7453eb')
    def test_list_images_param_disk_format(self):
        # Test to get all images with disk_format = raw
        params = {"disk_format": "raw"}
        self._list_by_param_value_and_assert(params)

    @test.idempotent_id('7a95bb92-d99e-4b12-9718-7bc6ab73e6d2')
    def test_list_images_param_visibility(self):
        # Test to get all images with visibility = private
        params = {"visibility": "private"}
        self._list_by_param_value_and_assert(params)

    @test.idempotent_id('cf1b9a48-8340-480e-af7b-fe7e17690876')
    def test_list_images_param_size(self):
        # Test to get all images by size
        image_id = self.created_images[0]
        # Get image metadata
        image = self.client.show_image(image_id)

        params = {"size": image['size']}
        self._list_by_param_value_and_assert(params)

    @test.idempotent_id('4ad8c157-971a-4ba8-aa84-ed61154b1e7f')
    def test_list_images_param_min_max_size(self):
        # Test to get all images with size between 2000 to 3000
        image_id = self.created_images[0]
        # Get image metadata
        image = self.client.show_image(image_id)

        size = image['size']
        params = {"size_min": size - 500, "size_max": size + 500}
        images_list = self.client.list_images(params=params)['images']
        image_size_list = map(lambda x: x['size'], images_list)

        for image_size in image_size_list:
            self.assertTrue(image_size >= params['size_min'] and
                            image_size <= params['size_max'],
                            "Failed to get images by size_min and size_max")

    @test.idempotent_id('7fc9e369-0f58-4d05-9aa5-0969e2d59d15')
    def test_list_images_param_status(self):
        # Test to get all active images
        params = {"status": "active"}
        self._list_by_param_value_and_assert(params)

    @test.idempotent_id('e914a891-3cc8-4b40-ad32-e0a39ffbddbb')
    def test_list_images_param_limit(self):
        # Test to get images by limit
        params = {"limit": 1}
        images_list = self.client.list_images(params=params)['images']

        self.assertEqual(len(images_list), params['limit'],
                         "Failed to get images by limit")

    @test.idempotent_id('622b925c-479f-4736-860d-adeaf13bc371')
    def test_get_image_schema(self):
        # Test to get image schema
        schema = "image"
        body = self.client.show_schema(schema)
        self.assertEqual("image", body['name'])

    @test.idempotent_id('25c8d7b2-df21-460f-87ac-93130bcdc684')
    def test_get_images_schema(self):
        # Test to get images schema
        schema = "images"
        body = self.client.show_schema(schema)
        self.assertEqual("images", body['name'])
