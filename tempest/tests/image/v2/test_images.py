# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack, LLC
# All Rights Reserved.
# Copyright 2013 IBM Corp
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

from tempest import clients
from tempest import exceptions
import tempest.test
from tempest.test import attr


class CreateRegisterImagesTest(tempest.test.BaseTestCase):

    """
    Here we test the registration and creation of images
    """

    @classmethod
    def setUpClass(cls):
        cls.os = clients.Manager()
        cls.client = cls.os.image_client_v2
        cls.created_images = []

    @classmethod
    def tearDownClass(cls):
        for image_id in cls.created_images:
            cls.client.delete(image_id)

    @attr(type='negative')
    def test_register_with_invalid_container_format(self):
        # Negative tests for invalid data supplied to POST /images
        self.assertRaises(exceptions.BadRequest, self.client.create_image,
                          'test', 'wrong', 'vhd')

    @attr(type='negative')
    def test_register_with_invalid_disk_format(self):
        self.assertRaises(exceptions.BadRequest, self.client.create_image,
                          'test', 'bare', 'wrong')

    @attr(type='image')
    def test_register_then_upload(self):
        # Register, then upload an image
        resp, body = self.client.create_image('New Name', 'bare', 'raw',
                                              is_public=True)
        self.assertTrue('id' in body)
        image_id = body.get('id')
        self.created_images.append(image_id)
        self.assertTrue('name' in body)
        self.assertEqual('New Name', body.get('name'))
        self.assertTrue('visibility' in body)
        self.assertTrue(body.get('visibility') == 'public')
        self.assertTrue('status' in body)
        self.assertEqual('queued', body.get('status'))

        # Now try uploading an image file
        image_file = StringIO.StringIO(('*' * 1024))
        resp, body = self.client.store_image(image_id, image_file)
        self.assertEqual(resp.status, 204)
        resp, body = self.client.get_image_metadata(image_id)
        self.assertTrue('size' in body)
        self.assertEqual(1024, body.get('size'))


class ListImagesTest(tempest.test.BaseTestCase):

    """
    Here we test the listing of image information
    """

    @classmethod
    def setUpClass(cls):
        cls.os = clients.Manager()
        cls.client = cls.os.image_client_v2
        cls.created_images = []

        # We add a few images here to test the listing functionality of
        # the images API
        for x in xrange(0, 10):
            cls.created_images.append(cls._create_standard_image(x))

    @classmethod
    def tearDownClass(cls):
        for image_id in cls.created_images:
            cls.client.delete_image(image_id)
            cls.client.wait_for_resource_deletion(image_id)

    @classmethod
    def _create_standard_image(cls, number):
        """
        Create a new standard image and return the ID of the newly-registered
        image. Note that the size of the new image is a random number between
        1024 and 4096
        """
        image_file = StringIO.StringIO('*' * random.randint(1024, 4096))
        name = 'New Standard Image %s' % number
        resp, body = cls.client.create_image(name, 'bare', 'raw',
                                             is_public=True)
        image_id = body['id']
        resp, body = cls.client.store_image(image_id, data=image_file)

        return image_id

    @attr(type='image')
    def test_index_no_params(self):
        # Simple test to see all fixture images returned
        resp, images_list = self.client.image_list()
        self.assertEqual(resp['status'], '200')
        image_list = map(lambda x: x['id'], images_list)
        for image in self.created_images:
            self.assertTrue(image in image_list)
