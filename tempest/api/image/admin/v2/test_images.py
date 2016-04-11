# Copyright 2015 Red Hat, Inc.
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

from six import moves
import testtools

from tempest.api.image import base
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import exceptions as lib_exc
from tempest import test

CONF = config.CONF


class BasicAdminOperationsImagesTest(base.BaseV2ImageAdminTest):
    """Here we test admin operations of images"""

    @testtools.skipUnless(CONF.image_feature_enabled.deactivate_image,
                          'deactivate-image is not available.')
    @test.idempotent_id('951ebe01-969f-4ea9-9898-8a3f1f442ab0')
    def test_admin_deactivate_reactivate_image(self):
        # Create image by non-admin tenant
        image_name = data_utils.rand_name('image')
        body = self.client.create_image(name=image_name,
                                        container_format='bare',
                                        disk_format='raw',
                                        visibility='private')
        image_id = body['id']
        self.addCleanup(self.client.delete_image, image_id)
        # upload an image file
        content = data_utils.random_bytes()
        image_file = moves.cStringIO(content)
        self.client.store_image_file(image_id, image_file)
        # deactivate image
        self.admin_client.deactivate_image(image_id)
        body = self.client.show_image(image_id)
        self.assertEqual("deactivated", body['status'])
        # non-admin user unable to download deactivated image
        self.assertRaises(lib_exc.Forbidden, self.client.show_image_file,
                          image_id)
        # reactivate image
        self.admin_client.reactivate_image(image_id)
        body = self.client.show_image(image_id)
        self.assertEqual("active", body['status'])
        # non-admin user able to download image after reactivation by admin
        body = self.client.show_image_file(image_id)
        self.assertEqual(content, body.data)
