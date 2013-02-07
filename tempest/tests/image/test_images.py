# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import testtools

from nose.plugins.attrib import attr


from tempest import clients
from tempest import exceptions


class CreateRegisterImagesTest(testtools.TestCase):

    """
    Here we test the registration and creation of images
    """

    @classmethod
    def setUpClass(cls):
        cls.os = clients.Manager()
        cls.client = cls.os.image_client
        cls.created_images = []

    @classmethod
    def tearDownClass(cls):
        for image_id in cls.created_images:
            cls.client.delete(image_id)

    @attr(type='negative')
    def test_register_with_invalid_container_format(self):
        # Negative tests for invalid data supplied to POST /images
        try:
            resp, body = self.client.create_image('test', 'wrong', 'vhd')
        except exceptions.BadRequest:
            pass
        else:
            self.fail('Invalid container format should not be accepted')

    @attr(type='negative')
    def test_register_with_invalid_disk_format(self):
        try:
            resp, body = self.client.create_image('test', 'bare', 'wrong')
        except exceptions.BadRequest:
                pass
        else:
            self.fail("Invalid disk format should not be accepted")

    @attr(type='image')
    def test_register_then_upload(self):
        # Register, then upload an image
        properties = {'prop1': 'val1'}
        resp, body = self.client.create_image('New Name', 'bare', 'raw',
                                              is_public=True,
                                              properties=properties)
        self.assertTrue('id' in body)
        image_id = body.get('id')
        self.created_images.append(image_id)
        self.assertTrue('name' in body)
        self.assertEqual('New Name', body.get('name'))
        self.assertTrue('is_public' in body)
        self.assertTrue(body.get('is_public'))
        self.assertTrue('status' in body)
        self.assertEqual('queued', body.get('status'))
        self.assertTrue('properties' in body)
        for key, val in properties.items():
            self.assertEqual(val, body.get('properties')[key])

        # Now try uploading an image file
        image_file = StringIO.StringIO(('*' * 1024))
        resp, body = self.client.update_image(image_id, data=image_file)
        self.assertTrue('size' in body)
        self.assertEqual(1024, body.get('size'))

    @attr(type='image')
    def test_register_remote_image(self):
        # Register a new remote image
        resp, body = self.client.create_image('New Remote Image', 'bare',
                                              'raw', is_public=True,
                                              location='http://example.com'
                                                       '/someimage.iso')
        self.assertTrue('id' in body)
        image_id = body.get('id')
        self.created_images.append(image_id)
        self.assertTrue('name' in body)
        self.assertEqual('New Remote Image', body.get('name'))
        self.assertTrue('is_public' in body)
        self.assertTrue(body.get('is_public'))
        self.assertTrue('status' in body)
        self.assertEqual('active', body.get('status'))


class ListImagesTest(testtools.TestCase):

    """
    Here we test the listing of image information
    """

    @classmethod
    def setUpClass(cls):
        cls.os = clients.Manager()
        cls.client = cls.os.image_client
        cls.created_images = []

        # We add a few images here to test the listing functionality of
        # the images API
        for x in xrange(0, 10):
            # We make even images remote and odd images standard
            if x % 2 == 0:
                cls.created_images.append(cls._create_remote_image(x))
            else:
                cls.created_images.append(cls._create_standard_image(x))

    @classmethod
    def tearDownClass(cls):
        for image_id in cls.created_images:
            cls.client.delete_image(image_id)
            cls.client.wait_for_resource_deletion(image_id)

    @classmethod
    def _create_remote_image(cls, x):
        """
        Create a new remote image and return the ID of the newly-registered
        image
        """
        name = 'New Remote Image %s' % x
        location = 'http://example.com/someimage_%s.iso' % x
        resp, body = cls.client.create_image(name, 'bare', 'raw',
                                             is_public=True,
                                             location=location)
        image_id = body['id']
        return image_id

    @classmethod
    def _create_standard_image(cls, x):
        """
        Create a new standard image and return the ID of the newly-registered
        image. Note that the size of the new image is a random number between
        1024 and 4096
        """
        image_file = StringIO.StringIO('*' * random.randint(1024, 4096))
        name = 'New Standard Image %s' % x
        resp, body = cls.client.create_image(name, 'bare', 'raw',
                                             is_public=True, data=image_file)
        image_id = body['id']
        return image_id

    @attr(type='image')
    def test_index_no_params(self):
        # Simple test to see all fixture images returned
        resp, images_list = self.client.image_list()
        self.assertEqual(resp['status'], '200')
        image_list = map(lambda x: x['id'], images_list)
        for image in self.created_images:
            self.assertTrue(image in image_list)
