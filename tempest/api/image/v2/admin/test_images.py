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

from tempest.api.image import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class BasicOperationsImagesAdminTest(base.BaseV2ImageAdminTest):

    @decorators.related_bug('1420008')
    @decorators.idempotent_id('646a6eaa-135f-4493-a0af-12583021224e')
    def test_create_image_owner_param(self):
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
