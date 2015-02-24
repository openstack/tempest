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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.image import base
from tempest import test


class ImageMembersNegativeTest(base.BaseV1ImageMembersTest):

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('147a9536-18e3-45da-91ea-b037a028f364')
    def test_add_member_with_non_existing_image(self):
        # Add member with non existing image.
        non_exist_image = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.add_member,
                          self.alt_tenant_id, non_exist_image)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('e1559f05-b667-4f1b-a7af-518b52dc0c0f')
    def test_delete_member_with_non_existing_image(self):
        # Delete member with non existing image.
        non_exist_image = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.delete_member,
                          self.alt_tenant_id, non_exist_image)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f5720333-dd69-4194-bb76-d2f048addd56')
    def test_delete_member_with_non_existing_tenant(self):
        # Delete member with non existing tenant.
        image_id = self._create_image()
        non_exist_tenant = data_utils.rand_uuid_hex()
        self.assertRaises(lib_exc.NotFound, self.client.delete_member,
                          non_exist_tenant, image_id)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('f25f89e4-0b6c-453b-a853-1f80b9d7ef26')
    def test_get_image_without_membership(self):
        # Image is hidden from another tenants.
        image_id = self._create_image()
        self.assertRaises(lib_exc.NotFound,
                          self.alt_img_cli.get_image,
                          image_id)
