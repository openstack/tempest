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

import unittest2 as unittest

from nose.plugins.attrib import attr
from nose.plugins.skip import SkipTest

GLANCE_INSTALLED = False
try:
    import glanceclient
    GLANCE_INSTALLED = True
except ImportError:
    pass

from tempest import openstack


class CreateRegisterImagesTest(unittest.TestCase):

    """
    Here we test the registration and creation of images
    """

    @classmethod
    def setUpClass(cls):
        if not GLANCE_INSTALLED:
            raise SkipTest('Glance not installed')
        cls.os = openstack.ServiceManager()
        cls.client = cls.os.images.get_client()
        cls.created_images = []

    @classmethod
    def tearDownClass(cls):
        for image_id in cls.created_images:
            cls.client.images.delete(image_id)

    @attr(type='image')
    def test_register_with_invalid_data(self):
        """Negative tests for invalid data supplied to POST /images"""

        metas = [
            {
                'id': '1'
            },  # Cannot specify ID in registration
            {
                'container_format': 'wrong',
            },  # Invalid container format
            {
                'disk_format': 'wrong',
            },  # Invalid disk format
        ]
        for meta in metas:
            try:
                self.client.images.create(**meta)
            except glanceclient.exc.HTTPBadRequest:
                continue
            self.fail("Did not raise Invalid for meta %s." % meta)

    @attr(type='image')
    def test_register_then_upload(self):
        """Register, then upload an image"""
        meta = {
            'name': 'New Name',
            'is_public': True,
            'disk_format': 'vhd',
            'container_format': 'bare',
            'properties': {'prop1': 'val1'}
        }
        results = self.client.images.create(**meta)
        self.assertTrue(hasattr(results, 'id'))
        image_id = results.id
        self.created_images.append(image_id)
        self.assertTrue(hasattr(results, 'name'))
        self.assertEqual(meta['name'], results.name)
        self.assertTrue(hasattr(results, 'is_public'))
        self.assertEqual(meta['is_public'], results.is_public)
        self.assertTrue(hasattr(results, 'status'))
        self.assertEqual('queued', results.status)
        self.assertTrue(hasattr(results, 'properties'))
        for key, val in meta['properties'].items():
            self.assertEqual(val, results.properties[key])

        # Now try uploading an image file
        image_file = StringIO.StringIO('*' * 1024)
        results = self.client.images.update(image_id, data=image_file)
        self.assertTrue(hasattr(results, 'status'))
        self.assertEqual('active', results.status)
        self.assertTrue(hasattr(results, 'size'))
        self.assertEqual(1024, results.size)

    @attr(type='image')
    def test_register_remote_image(self):
        """Register a new remote image"""
        meta = {
            'name': 'New Remote Image',
            'is_public': True,
            'disk_format': 'raw',
            'container_format': 'bare',
            'location': 'http://example.com/someimage.iso'
        }
        results = self.client.images.create(**meta)
        self.assertTrue(hasattr(results, 'id'))
        image_id = results.id
        self.created_images.append(image_id)
        self.assertTrue(hasattr(results, 'name'))
        self.assertEqual(meta['name'], results.name)
        self.assertTrue(hasattr(results, 'is_public'))
        self.assertEqual(meta['is_public'], results.is_public)
        self.assertTrue(hasattr(results, 'status'))
        self.assertEqual('active', results.status)


class ListImagesTest(unittest.TestCase):

    """
    Here we test the listing of image information
    """

    @classmethod
    def setUpClass(cls):
        if not GLANCE_INSTALLED:
            raise SkipTest('Glance not installed')
        cls.os = openstack.ServiceManager()
        cls.client = cls.os.images.get_client()
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
            cls.client.images.delete(image_id)

    @classmethod
    def _create_remote_image(cls, x):
        """
        Create a new remote image and return the ID of the newly-registered
        image
        """
        meta = {
            'name': 'New Remote Image %s' % x,
            'is_public': True,
            'disk_format': 'raw',
            'container_format': 'bare',
            'location': 'http://example.com/someimage_%s.iso' % x
        }
        results = cls.client.images.create(**meta)
        image_id = results.id
        return image_id

    @classmethod
    def _create_standard_image(cls, x):
        """
        Create a new standard image and return the ID of the newly-registered
        image. Note that the size of the new image is a random number between
        1024 and 4096
        """
        image_file = StringIO.StringIO('*' * random.randint(1024, 4096))
        meta = {
            'name': 'New Standard Image %s' % x,
            'is_public': True,
            'disk_format': 'raw',
            'container_format': 'bare',
            'data': image_file,
        }
        results = cls.client.images.create(**meta)
        image_id = results.id
        return image_id

    @attr(type='image')
    def test_index_no_params(self):
        """
        Simple test to see all fixture images returned
        """
        current_images = set(i.id for i in self.client.images.list())
        self.assertTrue(set(self.created_images) <= current_images)
