# Copyright 2018 Red Hat, Inc.
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

import io

from tempest.api.image import base
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc

CONF = config.CONF


class BasicOperationsImagesAdminTest(base.BaseV2ImageAdminTest):
    """"Test image operations about image owner"""

    @decorators.related_bug('1420008')
    @decorators.idempotent_id('646a6eaa-135f-4493-a0af-12583021224e')
    def test_create_image_owner_param(self):
        """Test creating image with specified owner"""
        # NOTE: Create image with owner different from tenant owner by
        # using "owner" parameter requires an admin privileges.
        random_id = data_utils.rand_uuid_hex()
        image = self.admin_client.create_image(
            container_format='bare', disk_format='raw', owner=random_id)
        self.addCleanup(self.admin_client.delete_image, image['id'])
        image_info = self.admin_client.show_image(image['id'])
        self.assertEqual(random_id, image_info['owner'])

    @decorators.related_bug('1420008')
    @decorators.idempotent_id('525ba546-10ef-4aad-bba1-1858095ce553')
    def test_update_image_owner_param(self):
        """Test updating image owner"""
        random_id_1 = data_utils.rand_uuid_hex()
        image = self.admin_client.create_image(
            container_format='bare', disk_format='raw', owner=random_id_1)
        self.addCleanup(self.admin_client.delete_image, image['id'])
        created_image_info = self.admin_client.show_image(image['id'])

        random_id_2 = data_utils.rand_uuid_hex()
        self.admin_client.update_image(
            image['id'], [dict(replace="/owner", value=random_id_2)])
        updated_image_info = self.admin_client.show_image(image['id'])

        self.assertEqual(random_id_2, updated_image_info['owner'])
        self.assertNotEqual(created_image_info['owner'],
                            updated_image_info['owner'])

    @decorators.idempotent_id('f6ab4aa0-035e-4664-9f2d-c57c6df50605')
    def test_list_public_image(self):
        """Test create image as admin and list public image as none admin"""
        name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix,
            name=self.__class__.__name__ + '-Image')
        image = self.admin_client.create_image(
            name=name,
            container_format='bare',
            visibility='public',
            disk_format='raw')
        waiters.wait_for_image_status(self.admin_client, image['id'], 'queued')
        created_image = self.admin_client.show_image(image['id'])
        self.assertEqual(image['id'], created_image['id'])
        self.addCleanup(self.admin_client.delete_image, image['id'])

        images_list = self.client.list_images()['images']
        fetched_images_id = [img['id'] for img in images_list]
        self.assertIn(image['id'], fetched_images_id)


class ImportCopyImagesTest(base.BaseV2ImageAdminTest):
    """Test the import copy-image operations"""

    @classmethod
    def skip_checks(cls):
        super(ImportCopyImagesTest, cls).skip_checks()
        if not CONF.image_feature_enabled.import_image:
            skip_msg = (
                "%s skipped as image import is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @decorators.idempotent_id('9b3b644e-03d1-11eb-a036-fa163e2eaf49')
    def test_image_copy_image_import(self):
        """Test 'copy-image' import functionalities

        Create image, import image with copy-image method and
        verify that import succeeded.
        """
        available_stores = self.get_available_stores()
        available_import_methods = self.client.info_import()[
            'import-methods']['value']
        # NOTE(gmann): Skip if copy-image import method and multistore
        # are not available.
        if ('copy-image' not in available_import_methods or
            not available_stores):
            raise self.skipException('Either copy-image import method or '
                                     'multistore is not available')
        uuid = data_utils.rand_uuid()
        image_name = data_utils.rand_name(
            prefix=CONF.resource_name_prefix, name='copy-image')
        container_format = CONF.image.container_formats[0]
        disk_format = 'raw'
        image = self.create_image(name=image_name,
                                  container_format=container_format,
                                  disk_format=disk_format,
                                  visibility='private',
                                  ramdisk_id=uuid)
        self.assertEqual('queued', image['status'])

        file_content = data_utils.random_bytes()
        image_file = io.BytesIO(file_content)
        self.client.store_image_file(image['id'], image_file)

        body = self.client.show_image(image['id'])
        self.assertEqual(image['id'], body['id'])
        self.assertEqual(len(file_content), body.get('size'))
        self.assertEqual('active', body['status'])

        # Copy image to all the stores. In case of all_stores request
        # glance will skip the stores where image is already available.
        self.admin_client.image_import(image['id'], method='copy-image',
                                       all_stores=True,
                                       all_stores_must_succeed=False)

        # Wait for copy to finished on all stores.
        failed_stores = waiters.wait_for_image_copied_to_stores(
            self.client, image['id'])
        # Assert if copy is failed on any store.
        self.assertEqual(0, len(failed_stores),
                         "Failed to copy the following stores: %s" %
                         str(failed_stores))


class ImageLocationsAdminTest(base.BaseV2ImageAdminTest):

    @classmethod
    def skip_checks(cls):
        super(ImageLocationsAdminTest, cls).skip_checks()
        if not CONF.image_feature_enabled.manage_locations:
            skip_msg = (
                "%s skipped as show_multiple_locations is not available" % (
                    cls.__name__))
            raise cls.skipException(skip_msg)

    @decorators.idempotent_id('8a648de4-b745-4c28-a7b5-20de1c3da4d2')
    def test_delete_locations(self):
        image = self.check_set_multiple_locations()
        expected_remaining_loc = image['locations'][1]

        self.admin_client.update_image(image['id'], [
            dict(remove='/locations/0')])

        # The image should now have only the one location we did not delete
        image = self.client.show_image(image['id'])
        self.assertEqual(1, len(image['locations']),
                         'Image should have one location but has %i' % (
                         len(image['locations'])))
        self.assertEqual(expected_remaining_loc['url'],
                         image['locations'][0]['url'])

        # The direct_url should now be the last remaining location
        if 'direct_url' in image:
            self.assertEqual(image['direct_url'], image['locations'][0]['url'])

        # Removing the last location should be disallowed
        self.assertRaises(lib_exc.Forbidden,
                          self.admin_client.update_image, image['id'], [
                              dict(remove='/locations/0')])


class MultiStoresImagesTest(base.BaseV2ImageAdminTest, base.BaseV2ImageTest):
    """Test importing and deleting image in multiple stores"""
    @classmethod
    def skip_checks(cls):
        super(MultiStoresImagesTest, cls).skip_checks()
        if not CONF.image_feature_enabled.import_image:
            skip_msg = (
                "%s skipped as image import is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @classmethod
    def resource_setup(cls):
        super(MultiStoresImagesTest, cls).resource_setup()
        cls.available_import_methods = \
            cls.client.info_import()['import-methods']['value']
        if not cls.available_import_methods:
            raise cls.skipException('Server does not support '
                                    'any import method')

        # NOTE(pdeore): Skip if glance-direct import method and mutlistore
        # are not enabled/configured, or only one store is configured in
        # multiple stores setup.
        cls.available_stores = cls.get_available_stores()
        if ('glance-direct' not in cls.available_import_methods or
                not len(cls.available_stores) > 1):
            raise cls.skipException(
                'Either glance-direct import method not present in %s or '
                'None or only one store is '
                'configured %s' % (cls.available_import_methods,
                                   cls.available_stores))

    @decorators.idempotent_id('1ecec683-41d4-4470-a0df-54969ec74514')
    def test_delete_image_from_specific_store(self):
        """Test delete image from specific store"""
        # Import image to available stores
        image, stores = self.create_and_stage_image(all_stores=True)
        self.client.image_import(image['id'],
                                 method='glance-direct',
                                 all_stores=True)
        self.addCleanup(self.admin_client.delete_image, image['id'])
        waiters.wait_for_image_imported_to_stores(
            self.client,
            image['id'], stores)
        observed_image = self.client.show_image(image['id'])

        # Image will be deleted from first store
        first_image_store_deleted = (observed_image['stores'].split(","))[0]
        self.admin_client.delete_image_from_store(
            observed_image['id'], first_image_store_deleted)
        waiters.wait_for_image_deleted_from_store(
            self.admin_client,
            observed_image,
            stores,
            first_image_store_deleted)
