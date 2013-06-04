# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 OpenStack, LLC
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

import cStringIO as StringIO
import random

from tempest.api.image import base
from tempest import exceptions
from tempest.test import attr


class CreateRegisterImagesTest(base.BaseV2ImageTest):

    """
    Here we test the registration and creation of images
    """

    @attr(type='gate')
    def test_register_with_invalid_container_format(self):
        # Negative tests for invalid data supplied to POST /images
        self.assertRaises(exceptions.BadRequest, self.client.create_image,
                          'test', 'wrong', 'vhd')

    @attr(type='gate')
    def test_register_with_invalid_disk_format(self):
        self.assertRaises(exceptions.BadRequest, self.client.create_image,
                          'test', 'bare', 'wrong')

    @attr(type='gate')
    def test_register_then_upload(self):
        # Register, then upload an image
        resp, body = self.create_image(name='New Name',
                                       container_format='bare',
                                       disk_format='raw',
                                       visibility='public')
        self.assertTrue('id' in body)
        image_id = body.get('id')
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


class ListImagesTest(base.BaseV2ImageTest):

    """
    Here we test the listing of image information
    """

    @classmethod
    def setUpClass(cls):
        super(ListImagesTest, cls).setUpClass()
        # We add a few images here to test the listing functionality of
        # the images API
        for x in xrange(0, 10):
            cls._create_standard_image(x)

    @classmethod
    def _create_standard_image(cls, number):
        """
        Create a new standard image and return the ID of the newly-registered
        image. Note that the size of the new image is a random number between
        1024 and 4096
        """
        image_file = StringIO.StringIO('*' * random.randint(1024, 4096))
        name = 'New Standard Image %s' % number
        resp, body = cls.create_image(name=name, container_format='bare',
                                      disk_format='raw',
                                      visibility='public')
        image_id = body['id']
        resp, body = cls.client.store_image(image_id, data=image_file)

        return image_id

    @attr(type='gate')
    def test_index_no_params(self):
        # Simple test to see all fixture images returned
        resp, images_list = self.client.image_list()
        self.assertEqual(resp['status'], '200')
        image_list = map(lambda x: x['id'], images_list)
        for image in self.created_images:
            self.assertTrue(image in image_list)
