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

import six

from tempest.api.image import base
from tempest.common import image as common_image
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions

CONF = config.CONF


def get_container_and_disk_format():
    a_formats = ['ami', 'ari', 'aki']

    container_format = CONF.image.container_formats[0]

    # In v1, If container_format is one of ['ami', 'ari', 'aki'], then
    # disk_format must be same with container_format.
    # If they are of different item sequence in tempest.conf, such as:
    #     container_formats = ami,ari,aki,bare
    #     disk_formats = ari,ami,aki,vhd
    # we can select one in disk_format list that is same with container_format.
    if container_format in a_formats:
        if container_format in CONF.image.disk_formats:
            disk_format = container_format
        else:
            msg = ("The container format and the disk format don't match. "
                   "Container format: %(container)s, Disk format: %(disk)s." %
                   {'container': container_format, 'disk':
                       CONF.image.disk_formats})
            raise exceptions.InvalidConfiguration(msg)
    else:
        disk_format = CONF.image.disk_formats[0]

    return container_format, disk_format


class CreateRegisterImagesTest(base.BaseV1ImageTest):
    """Here we test the registration and creation of images."""

    @decorators.idempotent_id('3027f8e6-3492-4a11-8575-c3293017af4d')
    def test_register_then_upload(self):
        # Register, then upload an image
        properties = {'prop1': 'val1'}
        container_format, disk_format = get_container_and_disk_format()
        image = self.create_image(name='New Name',
                                  container_format=container_format,
                                  disk_format=disk_format,
                                  is_public=False,
                                  properties=properties)
        self.assertEqual('New Name', image.get('name'))
        self.assertFalse(image.get('is_public'))
        self.assertEqual('queued', image.get('status'))
        for key, val in properties.items():
            self.assertEqual(val, image.get('properties')[key])

        # Now try uploading an image file
        image_file = six.BytesIO(data_utils.random_bytes())
        body = self.client.update_image(image['id'], data=image_file)['image']
        self.assertIn('size', body)
        self.assertEqual(1024, body.get('size'))

    @decorators.idempotent_id('69da74d9-68a9-404b-9664-ff7164ccb0f5')
    def test_register_remote_image(self):
        # Register a new remote image
        container_format, disk_format = get_container_and_disk_format()
        body = self.create_image(name='New Remote Image',
                                 container_format=container_format,
                                 disk_format=disk_format, is_public=False,
                                 location=CONF.image.http_image,
                                 properties={'key1': 'value1',
                                             'key2': 'value2'})
        self.assertEqual('New Remote Image', body.get('name'))
        self.assertFalse(body.get('is_public'))
        self.assertEqual('active', body.get('status'))
        properties = body.get('properties')
        self.assertEqual(properties['key1'], 'value1')
        self.assertEqual(properties['key2'], 'value2')

    @decorators.idempotent_id('6d0e13a7-515b-460c-b91f-9f4793f09816')
    def test_register_http_image(self):
        container_format, disk_format = get_container_and_disk_format()
        image = self.create_image(name='New Http Image',
                                  container_format=container_format,
                                  disk_format=disk_format, is_public=False,
                                  copy_from=CONF.image.http_image)
        self.assertEqual('New Http Image', image.get('name'))
        self.assertFalse(image.get('is_public'))
        waiters.wait_for_image_status(self.client, image['id'], 'active')
        self.client.show_image(image['id'])

    @decorators.idempotent_id('05b19d55-140c-40d0-b36b-fafd774d421b')
    def test_register_image_with_min_ram(self):
        # Register an image with min ram
        container_format, disk_format = get_container_and_disk_format()
        properties = {'prop1': 'val1'}
        body = self.create_image(name='New_image_with_min_ram',
                                 container_format=container_format,
                                 disk_format=disk_format,
                                 is_public=False,
                                 min_ram=40,
                                 properties=properties)
        self.assertEqual('New_image_with_min_ram', body.get('name'))
        self.assertFalse(body.get('is_public'))
        self.assertEqual('queued', body.get('status'))
        self.assertEqual(40, body.get('min_ram'))
        for key, val in properties.items():
            self.assertEqual(val, body.get('properties')[key])
        self.client.delete_image(body['id'])


class ListImagesTest(base.BaseV1ImageTest):
    """Here we test the listing of image information"""

    @classmethod
    def skip_checks(cls):
        super(ListImagesTest, cls).skip_checks()
        if (len(CONF.image.container_formats) < 2 or
                len(CONF.image.disk_formats) < 2):
            skip_msg = ("%s skipped as multiple container formats "
                        "or disk formats are not available." % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def resource_setup(cls):
        super(ListImagesTest, cls).resource_setup()
        # We add a few images here to test the listing functionality of
        # the images API
        a_formats = ['ami', 'ari', 'aki']

        (cls.container_format,
         container_format_alt) = CONF.image.container_formats[:2]
        cls.disk_format, cls.disk_format_alt = CONF.image.disk_formats[:2]
        if cls.container_format in a_formats:
            cls.disk_format = cls.container_format
        if container_format_alt in a_formats:
            cls.disk_format_alt = container_format_alt

        img1 = cls._create_remote_image('one', cls.container_format,
                                        cls.disk_format)
        img2 = cls._create_remote_image('two', container_format_alt,
                                        cls.disk_format_alt)
        img3 = cls._create_remote_image('dup', cls.container_format,
                                        cls.disk_format)
        img4 = cls._create_remote_image('dup', cls.container_format,
                                        cls.disk_format)
        img5 = cls._create_standard_image('1', container_format_alt,
                                          cls.disk_format_alt, 42)
        img6 = cls._create_standard_image('2', container_format_alt,
                                          cls.disk_format_alt, 142)
        img7 = cls._create_standard_image('33', cls.container_format,
                                          cls.disk_format, 142)
        img8 = cls._create_standard_image('33', cls.container_format,
                                          cls.disk_format, 142)
        cls.created_set = set(cls.created_images)
        # same container format
        cls.same_container_format_set = set((img1, img3, img4, img7, img8))
        # same disk format
        cls.same_disk_format_set = set((img2, img5, img6))

        # 1x with size 42
        cls.size42_set = set((img5,))
        # 3x with size 142
        cls.size142_set = set((img6, img7, img8,))
        # dup named
        cls.dup_set = set((img3, img4))

    @classmethod
    def _create_remote_image(cls, name, container_format, disk_format):
        """Create a new remote image and return newly-registered image-id"""

        name = 'New Remote Image %s' % name
        location = CONF.image.http_image
        image = cls.create_image(name=name,
                                 container_format=container_format,
                                 disk_format=disk_format,
                                 is_public=False,
                                 location=location)
        return image['id']

    @classmethod
    def _create_standard_image(cls, name, container_format,
                               disk_format, size):
        """Create a new standard image and return newly-registered image-id

        Note that the size of the new image is a random number between
        1024 and 4096
        """
        image_file = six.BytesIO(data_utils.random_bytes(size))
        name = 'New Standard Image %s' % name
        image = cls.create_image(name=name,
                                 container_format=container_format,
                                 disk_format=disk_format,
                                 is_public=False, data=image_file)
        return image['id']

    @decorators.idempotent_id('246178ab-3b33-4212-9a4b-a7fe8261794d')
    def test_index_no_params(self):
        # Simple test to see all fixture images returned
        images_list = self.client.list_images()['images']
        image_list = [image['id'] for image in images_list]
        for image_id in self.created_images:
            self.assertIn(image_id, image_list)

    @decorators.idempotent_id('f1755589-63d6-4468-b098-589820eb4031')
    def test_index_disk_format(self):
        images_list = self.client.list_images(
            disk_format=self.disk_format_alt)['images']
        for image in images_list:
            self.assertEqual(image['disk_format'], self.disk_format_alt)
        result_set = set(map(lambda x: x['id'], images_list))
        self.assertTrue(self.same_disk_format_set <= result_set)
        self.assertFalse(self.created_set - self.same_disk_format_set <=
                         result_set)

    @decorators.idempotent_id('2143655d-96d9-4bec-9188-8674206b4b3b')
    def test_index_container_format(self):
        images_list = self.client.list_images(
            container_format=self.container_format)['images']
        for image in images_list:
            self.assertEqual(image['container_format'], self.container_format)
        result_set = set(map(lambda x: x['id'], images_list))
        self.assertTrue(self.same_container_format_set <= result_set)
        self.assertFalse(self.created_set - self.same_container_format_set <=
                         result_set)

    @decorators.idempotent_id('feb32ac6-22bb-4a16-afd8-9454bb714b14')
    def test_index_max_size(self):
        images_list = self.client.list_images(size_max=42)['images']
        for image in images_list:
            self.assertLessEqual(image['size'], 42)
        result_set = set(map(lambda x: x['id'], images_list))
        self.assertTrue(self.size42_set <= result_set)
        self.assertFalse(self.created_set - self.size42_set <= result_set)

    @decorators.idempotent_id('6ffc16d0-4cbf-4401-95c8-4ac63eac34d8')
    def test_index_min_size(self):
        images_list = self.client.list_images(size_min=142)['images']
        for image in images_list:
            self.assertGreaterEqual(image['size'], 142)
        result_set = set(map(lambda x: x['id'], images_list))
        self.assertTrue(self.size142_set <= result_set)
        self.assertFalse(self.size42_set <= result_set)

    @decorators.idempotent_id('e5dc26d9-9aa2-48dd-bda5-748e1445da98')
    def test_index_status_active_detail(self):
        images_list = self.client.list_images(detail=True,
                                              status='active',
                                              sort_key='size',
                                              sort_dir='desc')['images']
        top_size = images_list[0]['size']  # We have non-zero sized images
        for image in images_list:
            size = image['size']
            self.assertLessEqual(size, top_size)
            top_size = size
            self.assertEqual(image['status'], 'active')

    @decorators.idempotent_id('097af10a-bae8-4342-bff4-edf89969ed2a')
    def test_index_name(self):
        images_list = self.client.list_images(
            detail=True,
            name='New Remote Image dup')['images']
        result_set = set(map(lambda x: x['id'], images_list))
        for image in images_list:
            self.assertEqual(image['name'], 'New Remote Image dup')
        self.assertTrue(self.dup_set <= result_set)
        self.assertFalse(self.created_set - self.dup_set <= result_set)


class UpdateImageMetaTest(base.BaseV1ImageTest):
    @classmethod
    def resource_setup(cls):
        super(UpdateImageMetaTest, cls).resource_setup()
        container_format, disk_format = get_container_and_disk_format()
        cls.image_id = cls._create_standard_image('1', container_format,
                                                  disk_format, 42)

    @classmethod
    def _create_standard_image(cls, name, container_format,
                               disk_format, size):
        """Create a new standard image and return newly-registered image-id"""

        image_file = six.BytesIO(data_utils.random_bytes(size))
        name = 'New Standard Image %s' % name
        image = cls.create_image(name=name,
                                 container_format=container_format,
                                 disk_format=disk_format,
                                 is_public=False, data=image_file,
                                 properties={'key1': 'value1'})
        return image['id']

    @decorators.idempotent_id('01752c1c-0275-4de3-9e5b-876e44541928')
    def test_list_image_metadata(self):
        # All metadata key/value pairs for an image should be returned
        resp = self.client.check_image(self.image_id)
        resp_metadata = common_image.get_image_meta_from_headers(resp)
        expected = {'key1': 'value1'}
        self.assertEqual(expected, resp_metadata['properties'])

    @decorators.idempotent_id('d6d7649c-08ce-440d-9ea7-e3dda552f33c')
    def test_update_image_metadata(self):
        # The metadata for the image should match the updated values
        req_metadata = {'key1': 'alt1', 'key2': 'value2'}
        resp = self.client.check_image(self.image_id)
        metadata = common_image.get_image_meta_from_headers(resp)
        self.assertEqual(metadata['properties'], {'key1': 'value1'})
        metadata['properties'].update(req_metadata)
        headers = common_image.image_meta_to_headers(
            properties=metadata['properties'])
        self.client.update_image(self.image_id, headers=headers)
        resp = self.client.check_image(self.image_id)
        resp_metadata = common_image.get_image_meta_from_headers(resp)
        self.assertEqual(req_metadata, resp_metadata['properties'])
