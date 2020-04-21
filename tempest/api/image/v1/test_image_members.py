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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class ImageMembersTest(base.BaseV1ImageMembersTest):
    """Test image members"""

    @decorators.idempotent_id('1d6ef640-3a20-4c84-8710-d95828fdb6ad')
    def test_add_image_member(self):
        """Test adding member for image"""
        image = self._create_image()
        self.image_member_client.create_image_member(image, self.alt_tenant_id)
        body = self.image_member_client.list_image_members(image)
        members = body['members']
        members = [member['member_id'] for member in members]
        self.assertIn(self.alt_tenant_id, members)
        # get image as alt user
        self.alt_img_cli.show_image(image)

    @decorators.idempotent_id('6a5328a5-80e8-4b82-bd32-6c061f128da9')
    def test_get_shared_images(self):
        """Test getting shared images"""
        image = self._create_image()
        self.image_member_client.create_image_member(image, self.alt_tenant_id)
        share_image = self._create_image()
        self.image_member_client.create_image_member(share_image,
                                                     self.alt_tenant_id)
        body = self.image_member_client.list_shared_images(
            self.alt_tenant_id)
        images = body['shared_images']
        images = [img['image_id'] for img in images]
        self.assertIn(share_image, images)
        self.assertIn(image, images)

    @decorators.idempotent_id('a76a3191-8948-4b44-a9d6-4053e5f2b138')
    def test_remove_member(self):
        """Test removing member from image"""
        image_id = self._create_image()
        self.image_member_client.create_image_member(image_id,
                                                     self.alt_tenant_id)
        self.image_member_client.delete_image_member(image_id,
                                                     self.alt_tenant_id)
        body = self.image_member_client.list_image_members(image_id)
        members = body['members']
        self.assertEmpty(members)
        self.assertRaises(
            lib_exc.NotFound, self.alt_img_cli.show_image, image_id)
