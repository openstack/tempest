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
        image_name = data_utils.rand_name('copy-image')
        container_format = CONF.image.container_formats[0]
        disk_format = CONF.image.disk_formats[0]
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
