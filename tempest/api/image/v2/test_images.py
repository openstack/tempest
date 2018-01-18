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

import six

from oslo_log import log as logging
from tempest.api.image import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF
LOG = logging.getLogger(__name__)


class BasicOperationsImagesTest(base.BaseV2ImageTest):
    """Here we test the basic operations of images"""

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('139b765e-7f3d-4b3d-8b37-3ca3876ee318')
    def test_register_upload_get_image_file(self):
        """Here we test these functionalities

        Register image, upload the image file, get image and get image
        file api's
        """

        uuid = '00000000-1111-2222-3333-444455556666'
        image_name = data_utils.rand_name('image')
        container_format = CONF.image.container_formats[0]
        disk_format = CONF.image.disk_formats[0]
        image = self.create_image(name=image_name,
                                  container_format=container_format,
                                  disk_format=disk_format,
                                  visibility='private',
                                  ramdisk_id=uuid)
        self.assertIn('name', image)
        self.assertEqual(image_name, image['name'])
        self.assertIn('visibility', image)
        self.assertEqual('private', image['visibility'])
        self.assertIn('status', image)
        self.assertEqual('queued', image['status'])

        # Now try uploading an image file
        file_content = data_utils.random_bytes()
        image_file = six.BytesIO(file_content)
        self.client.store_image_file(image['id'], image_file)

        # Now try to get image details
        body = self.client.show_image(image['id'])
        self.assertEqual(image['id'], body['id'])
        self.assertEqual(image_name, body['name'])
        self.assertEqual(uuid, body['ramdisk_id'])
        self.assertIn('size', body)
        self.assertEqual(1024, body.get('size'))

        # Now try get image file
        body = self.client.show_image_file(image['id'])
        self.assertEqual(file_content, body.data)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('f848bb94-1c6e-45a4-8726-39e3a5b23535')
    def test_delete_image(self):
        # Deletes an image by image_id

        # Create image
        image_name = data_utils.rand_name('image')
        container_format = CONF.image.container_formats[0]
        disk_format = CONF.image.disk_formats[0]
        image = self.create_image(name=image_name,
                                  container_format=container_format,
                                  disk_format=disk_format,
                                  visibility='private')
        # Delete Image
        self.client.delete_image(image['id'])
        self.client.wait_for_resource_deletion(image['id'])

        # Verifying deletion
        images = self.client.list_images()['images']
        images_id = [item['id'] for item in images]
        self.assertNotIn(image['id'], images_id)

    @decorators.attr(type='smoke')
    @decorators.idempotent_id('f66891a7-a35c-41a8-b590-a065c2a1caa6')
    def test_update_image(self):
        # Updates an image by image_id

        # Create image
        image_name = data_utils.rand_name('image')
        container_format = CONF.image.container_formats[0]
        disk_format = CONF.image.disk_formats[0]
        image = self.create_image(name=image_name,
                                  container_format=container_format,
                                  disk_format=disk_format,
                                  visibility='private')
        self.assertEqual('queued', image['status'])

        # Now try uploading an image file
        image_file = six.BytesIO(data_utils.random_bytes())
        self.client.store_image_file(image['id'], image_file)

        # Update Image
        new_image_name = data_utils.rand_name('new-image')
        self.client.update_image(image['id'], [
            dict(replace='/name', value=new_image_name)])

        # Verifying updating

        body = self.client.show_image(image['id'])
        self.assertEqual(image['id'], body['id'])
        self.assertEqual(new_image_name, body['name'])

    @decorators.idempotent_id('951ebe01-969f-4ea9-9898-8a3f1f442ab0')
    def test_deactivate_reactivate_image(self):
        # Create image
        image_name = data_utils.rand_name('image')
        image = self.create_image(name=image_name,
                                  container_format='bare',
                                  disk_format='raw',
                                  visibility='private')

        # Upload an image file
        content = data_utils.random_bytes()
        image_file = six.BytesIO(content)
        self.client.store_image_file(image['id'], image_file)

        # Deactivate image
        self.client.deactivate_image(image['id'])
        body = self.client.show_image(image['id'])
        self.assertEqual("deactivated", body['status'])

        # User unable to download deactivated image
        self.assertRaises(lib_exc.Forbidden, self.client.show_image_file,
                          image['id'])

        # Reactivate image
        self.client.reactivate_image(image['id'])
        body = self.client.show_image(image['id'])
        self.assertEqual("active", body['status'])

        # User able to download image after reactivation
        body = self.client.show_image_file(image['id'])
        self.assertEqual(content, body.data)


class ListUserImagesTest(base.BaseV2ImageTest):
    """Here we test the listing of image information"""

    @classmethod
    def resource_setup(cls):
        super(ListUserImagesTest, cls).resource_setup()
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
        image_file = six.BytesIO(data_utils.random_bytes(size))
        tags = [data_utils.rand_name('tag'), data_utils.rand_name('tag')]
        image = cls.create_image(container_format=container_format,
                                 disk_format=disk_format,
                                 visibility='private',
                                 tags=tags)
        cls.client.store_image_file(image['id'], data=image_file)
        # Keep the data of one test image so it can be used to filter lists
        cls.test_data = image

        return image['id']

    def _list_by_param_value_and_assert(self, params):
        """Perform list action with given params and validates result."""
        # Retrieve the list of images that meet the filter
        images_list = self.client.list_images(params=params)['images']
        # Validating params of fetched images
        msg = 'No images were found that met the filter criteria.'
        self.assertNotEmpty(images_list, msg)
        for image in images_list:
            for key in params:
                msg = "Failed to list images by %s" % key
                self.assertEqual(params[key], image[key], msg)

    def _list_sorted_by_image_size_and_assert(self, params, desc=False):
        """Validate an image list that has been sorted by size

        Perform list action with given params and validates the results are
        sorted by image size in either ascending or descending order.
        """
        # Retrieve the list of images that meet the filter
        images_list = self.client.list_images(params=params)['images']
        # Validate that the list was fetched sorted accordingly
        msg = 'No images were found that met the filter criteria.'
        self.assertNotEmpty(images_list, msg)
        sorted_list = [image['size'] for image in images_list]
        msg = 'The list of images was not sorted correctly.'
        self.assertEqual(sorted(sorted_list, reverse=desc), sorted_list, msg)

    @decorators.idempotent_id('1e341d7a-90a9-494c-b143-2cdf2aeb6aee')
    def test_list_no_params(self):
        # Simple test to see all fixture images returned
        images_list = self.client.list_images()['images']
        image_list = [image['id'] for image in images_list]

        for image in self.created_images:
            self.assertIn(image, image_list)

    @decorators.idempotent_id('9959ca1d-1aa7-4b7a-a1ea-0fff0499b37e')
    def test_list_images_param_container_format(self):
        # Test to get all images with a specific container_format
        params = {"container_format": self.test_data['container_format']}
        self._list_by_param_value_and_assert(params)

    @decorators.idempotent_id('4a4735a7-f22f-49b6-b0d9-66e1ef7453eb')
    def test_list_images_param_disk_format(self):
        # Test to get all images with disk_format = raw
        params = {"disk_format": "raw"}
        self._list_by_param_value_and_assert(params)

    @decorators.idempotent_id('7a95bb92-d99e-4b12-9718-7bc6ab73e6d2')
    def test_list_images_param_visibility(self):
        # Test to get all images with visibility = private
        params = {"visibility": "private"}
        self._list_by_param_value_and_assert(params)

    @decorators.idempotent_id('cf1b9a48-8340-480e-af7b-fe7e17690876')
    def test_list_images_param_size(self):
        # Test to get all images by size
        image_id = self.created_images[0]
        # Get image metadata
        image = self.client.show_image(image_id)

        params = {"size": image['size']}
        self._list_by_param_value_and_assert(params)

    @decorators.idempotent_id('4ad8c157-971a-4ba8-aa84-ed61154b1e7f')
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
            self.assertGreaterEqual(image_size, params['size_min'],
                                    "Failed to get images by size_min")
            self.assertLessEqual(image_size, params['size_max'],
                                 "Failed to get images by size_max")

    @decorators.idempotent_id('7fc9e369-0f58-4d05-9aa5-0969e2d59d15')
    def test_list_images_param_status(self):
        # Test to get all active images
        params = {"status": "active"}
        self._list_by_param_value_and_assert(params)

    @decorators.idempotent_id('e914a891-3cc8-4b40-ad32-e0a39ffbddbb')
    def test_list_images_param_limit(self):
        # Test to get images by limit
        params = {"limit": 1}
        images_list = self.client.list_images(params=params)['images']

        self.assertEqual(len(images_list), params['limit'],
                         "Failed to get images by limit")

    @decorators.idempotent_id('e9a44b91-31c8-4b40-a332-e0a39ffb4dbb')
    def test_list_image_param_owner(self):
        # Test to get images by owner
        image_id = self.created_images[0]
        # Get image metadata
        image = self.client.show_image(image_id)

        params = {"owner": image['owner']}
        self._list_by_param_value_and_assert(params)

    @decorators.idempotent_id('55c8f5f5-bfed-409d-a6d5-4caeda985d7b')
    def test_list_images_param_name(self):
        # Test to get images by name
        params = {'name': self.test_data['name']}
        self._list_by_param_value_and_assert(params)

    @decorators.idempotent_id('aa8ac4df-cff9-418b-8d0f-dd9c67b072c9')
    def test_list_images_param_tag(self):
        # Test to get images matching a tag
        params = {'tag': self.test_data['tags'][0]}
        images_list = self.client.list_images(params=params)['images']
        # Validating properties of fetched images
        self.assertNotEmpty(images_list)
        for image in images_list:
            msg = ("The image {image_name} does not have the expected tag "
                   "{expected_tag} among its tags: {observerd_tags}."
                   .format(image_name=image['name'],
                           expected_tag=self.test_data['tags'][0],
                           observerd_tags=image['tags']))
            self.assertIn(self.test_data['tags'][0], image['tags'], msg)

    @decorators.idempotent_id('eeadce49-04e0-43b7-aec7-52535d903e7a')
    def test_list_images_param_sort(self):
        params = {'sort': 'size:desc'}
        self._list_sorted_by_image_size_and_assert(params, desc=True)

    @decorators.idempotent_id('9faaa0c2-c3a5-43e1-8f61-61c54b409a49')
    def test_list_images_param_sort_key_dir(self):
        params = {'sort_key': 'size', 'sort_dir': 'desc'}
        self._list_sorted_by_image_size_and_assert(params, desc=True)

    @decorators.idempotent_id('622b925c-479f-4736-860d-adeaf13bc371')
    def test_get_image_schema(self):
        # Test to get image schema
        schema = "image"
        body = self.schemas_client.show_schema(schema)
        self.assertEqual("image", body['name'])

    @decorators.idempotent_id('25c8d7b2-df21-460f-87ac-93130bcdc684')
    def test_get_images_schema(self):
        # Test to get images schema
        schema = "images"
        body = self.schemas_client.show_schema(schema)
        self.assertEqual("images", body['name'])


class ListSharedImagesTest(base.BaseV2ImageTest):
    """Here we test the listing of a shared image information"""

    credentials = ['primary', 'alt']

    @classmethod
    def setup_clients(cls):
        super(ListSharedImagesTest, cls).setup_clients()
        cls.image_member_client = cls.os_primary.image_member_client_v2
        cls.alt_img_client = cls.os_alt.image_client_v2

    @decorators.idempotent_id('3fa50be4-8e38-4c02-a8db-7811bb780122')
    def test_list_images_param_member_status(self):
        # Create an image to be shared using default visibility
        image_file = six.BytesIO(data_utils.random_bytes(2048))
        container_format = CONF.image.container_formats[0]
        disk_format = CONF.image.disk_formats[0]
        image = self.create_image(container_format=container_format,
                                  disk_format=disk_format)
        self.client.store_image_file(image['id'], data=image_file)

        # Share the image created with the alt user
        self.image_member_client.create_image_member(
            image_id=image['id'], member=self.alt_img_client.tenant_id)

        # As an image consumer you need to provide the member_status parameter
        # along with the visibility=shared parameter in order for it to show
        # results
        params = {'member_status': 'pending', 'visibility': 'shared'}
        fetched_images = self.alt_img_client.list_images(params)['images']
        self.assertEqual(1, len(fetched_images))
        self.assertEqual(image['id'], fetched_images[0]['id'])
