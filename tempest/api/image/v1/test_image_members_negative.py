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


from tempest.api.image import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest import test


class ImageMembersNegativeTest(base.BaseV1ImageMembersTest):

    @test.attr(type=['negative', 'gate'])
    def test_add_member_with_non_existing_image(self):
        # Add member with non existing image.
        non_exist_image = data_utils.rand_uuid()
        self.assertRaises(exceptions.NotFound, self.client.add_member,
                          self.alt_tenant_id, non_exist_image)

    @test.attr(type=['negative', 'gate'])
    def test_delete_member_with_non_existing_image(self):
        # Delete member with non existing image.
        non_exist_image = data_utils.rand_uuid()
        self.assertRaises(exceptions.NotFound, self.client.delete_member,
                          self.alt_tenant_id, non_exist_image)

    @test.attr(type=['negative', 'gate'])
    def test_delete_member_with_non_existing_tenant(self):
        # Delete member with non existing tenant.
        image_id = self._create_image()
        non_exist_tenant = data_utils.rand_uuid_hex()
        self.assertRaises(exceptions.NotFound, self.client.delete_member,
                          non_exist_tenant, image_id)

    @test.attr(type=['negative', 'gate'])
    def test_get_image_without_membership(self):
        # Image is hidden from another tenants.
        image_id = self._create_image()
        self.assertRaises(exceptions.NotFound,
                          self.alt_img_cli.get_image,
                          image_id)
