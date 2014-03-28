# Copyright 2012 OpenStack Foundation
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

from tempest.api.image import base
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class CreateRegisterImagesTest(base.BaseV1ImageTest):
    """Here we test the registration and creation of images."""

    @test.attr(type='gate')
    def test_register_then_upload(self):
        # Register, then upload an image
        properties = {'prop1': 'val1'}
        resp, body = self.create_image(name='New Name',
                                       container_format='bare',
                                       disk_format='raw',
                                       is_public=True,
                                       properties=properties)
        self.assertIn('id', body)
        image_id = body.get('id')
        self.assertEqual('New Name', body.get('name'))
        self.assertTrue(body.get('is_public'))
        self.assertEqual('queued', body.get('status'))
        for key, val in properties.items():
            self.assertEqual(val, body.get('properties')[key])

        # Now try uploading an image file
        image_file = StringIO.StringIO(('*' * 1024))
        resp, body = self.client.update_image(image_id, data=image_file)
        self.assertIn('size', body)
        self.assertEqual(1024, body.get('size'))

    @test.attr(type='gate')
    def test_register_remote_image(self):
        # Register a new remote image
        resp, body = self.create_image(name='New Remote Image',
                                       container_format='bare',
                                       disk_format='raw', is_public=True,
                                       location='http://example.com'
                                                '/someimage.iso',
                                       properties={'key1': 'value1',
                                                   'key2': 'value2'})
        self.assertIn('id', body)
        self.assertEqual('New Remote Image', body.get('name'))
        self.assertTrue(body.get('is_public'))
        self.assertEqual('active', body.get('status'))
        properties = body.get('properties')
        self.assertEqual(properties['key1'], 'value1')
        self.assertEqual(properties['key2'], 'value2')

    @test.attr(type='gate')
    def test_register_http_image(self):
        resp, body = self.create_image(name='New Http Image',
                                       container_format='bare',
                                       disk_format='raw', is_public=True,
                                       copy_from=CONF.image.http_image)
        self.assertIn('id', body)
        image_id = body.get('id')
        self.assertEqual('New Http Image', body.get('name'))
        self.assertTrue(body.get('is_public'))
        self.client.wait_for_image_status(image_id, 'active')
        resp, body = self.client.get_image(image_id)
        self.assertEqual(resp['status'], '200')

    @test.attr(type='gate')
    def test_register_image_with_min_ram(self):
        # Register an image with min ram
        properties = {'prop1': 'val1'}
        resp, body = self.create_image(name='New_image_with_min_ram',
                                       container_format='bare',
                                       disk_format='raw',
                                       is_public=True,
                                       min_ram=40,
                                       properties=properties)
        self.assertIn('id', body)
        self.assertEqual('New_image_with_min_ram', body.get('name'))
        self.assertTrue(body.get('is_public'))
        self.assertEqual('queued', body.get('status'))
        self.assertEqual(40, body.get('min_ram'))
        for key, val in properties.items():
            self.assertEqual(val, body.get('properties')[key])
        resp, body = self.client.delete_image(body['id'])
        self.assertEqual('200', resp['status'])


class ListImagesTest(base.BaseV1ImageTest):

    """
    Here we test the listing of image information
    """

    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(ListImagesTest, cls).setUpClass()
        # We add a few images here to test the listing functionality of
        # the images API
        img1 = cls._create_remote_image('one', 'bare', 'raw')
        img2 = cls._create_remote_image('two', 'ami', 'ami')
        img3 = cls._create_remote_image('dup', 'bare', 'raw')
        img4 = cls._create_remote_image('dup', 'bare', 'raw')
        img5 = cls._create_standard_image('1', 'ami', 'ami', 42)
        img6 = cls._create_standard_image('2', 'ami', 'ami', 142)
        img7 = cls._create_standard_image('33', 'bare', 'raw', 142)
        img8 = cls._create_standard_image('33', 'bare', 'raw', 142)
        cls.created_set = set(cls.created_images)
        # 4x-4x remote image
        cls.remote_set = set((img1, img2, img3, img4))
        cls.standard_set = set((img5, img6, img7, img8))
        # 5x bare, 3x ami
        cls.bare_set = set((img1, img3, img4, img7, img8))
        cls.ami_set = set((img2, img5, img6))
        # 1x with size 42
        cls.size42_set = set((img5,))
        # 3x with size 142
        cls.size142_set = set((img6, img7, img8,))
        # dup named
        cls.dup_set = set((img3, img4))

    @classmethod
    def _create_remote_image(cls, name, container_format, disk_format):
        """
        Create a new remote image and return the ID of the newly-registered
        image
        """
        name = 'New Remote Image %s' % name
        location = 'http://example.com/someimage_%s.iso' % name
        resp, image = cls.create_image(name=name,
                                       container_format=container_format,
                                       disk_format=disk_format,
                                       is_public=True,
                                       location=location)
        image_id = image['id']
        return image_id

    @classmethod
    def _create_standard_image(cls, name, container_format,
                               disk_format, size):
        """
        Create a new standard image and return the ID of the newly-registered
        image. Note that the size of the new image is a random number between
        1024 and 4096
        """
        image_file = StringIO.StringIO('*' * size)
        name = 'New Standard Image %s' % name
        resp, image = cls.create_image(name=name,
                                       container_format=container_format,
                                       disk_format=disk_format,
                                       is_public=True, data=image_file)
        image_id = image['id']
        return image_id

    @test.attr(type='gate')
    def test_index_no_params(self):
        # Simple test to see all fixture images returned
        resp, images_list = self.client.image_list()
        self.assertEqual(resp['status'], '200')
        image_list = map(lambda x: x['id'], images_list)
        for image_id in self.created_images:
            self.assertIn(image_id, image_list)

    @test.attr(type='gate')
    def test_index_disk_format(self):
        resp, images_list = self.client.image_list(disk_format='ami')
        self.assertEqual(resp['status'], '200')
        for image in images_list:
            self.assertEqual(image['disk_format'], 'ami')
        result_set = set(map(lambda x: x['id'], images_list))
        self.assertTrue(self.ami_set <= result_set)
        self.assertFalse(self.created_set - self.ami_set <= result_set)

    @test.attr(type='gate')
    def test_index_container_format(self):
        resp, images_list = self.client.image_list(container_format='bare')
        self.assertEqual(resp['status'], '200')
        for image in images_list:
            self.assertEqual(image['container_format'], 'bare')
        result_set = set(map(lambda x: x['id'], images_list))
        self.assertTrue(self.bare_set <= result_set)
        self.assertFalse(self.created_set - self.bare_set <= result_set)

    @test.attr(type='gate')
    def test_index_max_size(self):
        resp, images_list = self.client.image_list(size_max=42)
        self.assertEqual(resp['status'], '200')
        for image in images_list:
            self.assertTrue(image['size'] <= 42)
        result_set = set(map(lambda x: x['id'], images_list))
        self.assertTrue(self.size42_set <= result_set)
        self.assertFalse(self.created_set - self.size42_set <= result_set)

    @test.attr(type='gate')
    def test_index_min_size(self):
        resp, images_list = self.client.image_list(size_min=142)
        self.assertEqual(resp['status'], '200')
        for image in images_list:
            self.assertTrue(image['size'] >= 142)
        result_set = set(map(lambda x: x['id'], images_list))
        self.assertTrue(self.size142_set <= result_set)
        self.assertFalse(self.size42_set <= result_set)

    @test.attr(type='gate')
    def test_index_status_active_detail(self):
        resp, images_list = self.client.image_list_detail(status='active',
                                                          sort_key='size',
                                                          sort_dir='desc')
        self.assertEqual(resp['status'], '200')
        top_size = images_list[0]['size']  # We have non-zero sized images
        for image in images_list:
            size = image['size']
            self.assertTrue(size <= top_size)
            top_size = size
            self.assertEqual(image['status'], 'active')

    @test.attr(type='gate')
    def test_index_name(self):
        resp, images_list = self.client.image_list_detail(
            name='New Remote Image dup')
        self.assertEqual(resp['status'], '200')
        result_set = set(map(lambda x: x['id'], images_list))
        for image in images_list:
            self.assertEqual(image['name'], 'New Remote Image dup')
        self.assertTrue(self.dup_set <= result_set)
        self.assertFalse(self.created_set - self.dup_set <= result_set)


class ListSnapshotImagesTest(base.BaseV1ImageTest):
    @classmethod
    @test.safe_setup
    def setUpClass(cls):
        super(ListSnapshotImagesTest, cls).setUpClass()
        if not CONF.compute_feature_enabled.api_v3:
            cls.servers_client = cls.os.servers_client
        else:
            cls.servers_client = cls.os.servers_v3_client
        cls.servers = []
        # We add a few images here to test the listing functionality of
        # the images API
        cls.snapshot = cls._create_snapshot(
            'snapshot', CONF.compute.image_ref,
            CONF.compute.flavor_ref)
        cls.snapshot_set = set((cls.snapshot,))

        image_file = StringIO.StringIO('*' * 42)
        resp, image = cls.create_image(name="Standard Image",
                                       container_format='ami',
                                       disk_format='ami',
                                       is_public=True, data=image_file)
        cls.image_id = image['id']
        cls.client.wait_for_image_status(image['id'], 'active')

    @classmethod
    def tearDownClass(cls):
        for server in getattr(cls, "servers", []):
            cls.servers_client.delete_server(server['id'])
        super(ListSnapshotImagesTest, cls).tearDownClass()

    @classmethod
    def _create_snapshot(cls, name, image_id, flavor, **kwargs):
        resp, server = cls.servers_client.create_server(
            name, image_id, flavor, **kwargs)
        cls.servers.append(server)
        cls.servers_client.wait_for_server_status(
            server['id'], 'ACTIVE')
        resp, image = cls.servers_client.create_image(
            server['id'], name)
        image_id = data_utils.parse_image_id(resp['location'])
        cls.created_images.append(image_id)
        cls.client.wait_for_image_status(image_id,
                                         'active')
        return image_id

    @test.attr(type='gate')
    def test_index_server_id(self):
        # The images should contain images filtered by server id
        resp, images = self.client.image_list_detail(
            {'instance_uuid': self.servers[0]['id']})
        self.assertEqual(200, resp.status)
        result_set = set(map(lambda x: x['id'], images))
        self.assertEqual(self.snapshot_set, result_set)

    @test.attr(type='gate')
    def test_index_type(self):
        # The list of servers should be filtered by image type
        params = {'image_type': 'snapshot'}
        resp, images = self.client.image_list_detail(params)

        self.assertEqual(200, resp.status)
        result_set = set(map(lambda x: x['id'], images))
        self.assertIn(self.snapshot, result_set)

    @test.attr(type='gate')
    def test_index_limit(self):
        # Verify only the expected number of results are returned
        resp, images = self.client.image_list_detail(limit=1)

        self.assertEqual(200, resp.status)
        self.assertEqual(1, len(images))

    @test.attr(type='gate')
    def test_index_by_change_since(self):
        # Verify an update image is returned
        # Becoming ACTIVE will modify the updated time
        # Filter by the image's created time
        resp, image = self.client.get_image_meta(self.snapshot)
        self.assertEqual(200, resp.status)
        self.assertEqual(self.snapshot, image['id'])
        resp, images = self.client.image_list_detail(
            changes_since=image['updated_at'])

        self.assertEqual(200, resp.status)
        result_set = set(map(lambda x: x['id'], images))
        self.assertIn(self.image_id, result_set)
        self.assertNotIn(self.snapshot, result_set)


class UpdateImageMetaTest(base.BaseV1ImageTest):
    @classmethod
    def setUpClass(cls):
        super(UpdateImageMetaTest, cls).setUpClass()
        cls.image_id = cls._create_standard_image('1', 'ami', 'ami', 42)

    @classmethod
    def _create_standard_image(cls, name, container_format,
                               disk_format, size):
        """
        Create a new standard image and return the ID of the newly-registered
        image. Note that the size of the new image is a random number between
        1024 and 4096
        """
        image_file = StringIO.StringIO('*' * size)
        name = 'New Standard Image %s' % name
        resp, image = cls.create_image(name=name,
                                       container_format=container_format,
                                       disk_format=disk_format,
                                       is_public=True, data=image_file,
                                       properties={'key1': 'value1'})
        image_id = image['id']
        return image_id

    @test.attr(type='gate')
    def test_list_image_metadata(self):
        # All metadata key/value pairs for an image should be returned
        resp, resp_metadata = self.client.get_image_meta(self.image_id)
        expected = {'key1': 'value1'}
        self.assertEqual(expected, resp_metadata['properties'])

    @test.attr(type='gate')
    def test_update_image_metadata(self):
        # The metadata for the image should match the updated values
        req_metadata = {'key1': 'alt1', 'key2': 'value2'}
        resp, metadata = self.client.get_image_meta(self.image_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(metadata['properties'], {'key1': 'value1'})
        metadata['properties'].update(req_metadata)
        resp, metadata = self.client.update_image(
            self.image_id, properties=metadata['properties'])

        resp, resp_metadata = self.client.get_image_meta(self.image_id)
        expected = {'key1': 'alt1', 'key2': 'value2'}
        self.assertEqual(expected, resp_metadata['properties'])
