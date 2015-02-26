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
from tempest import test


class ImageMembersTest(base.BaseV1ImageMembersTest):

    @test.attr(type='gate')
    @test.idempotent_id('1d6ef640-3a20-4c84-8710-d95828fdb6ad')
    def test_add_image_member(self):
        image = self._create_image()
        self.client.add_member(self.alt_tenant_id, image)
        body = self.client.get_image_membership(image)
        members = body['members']
        members = map(lambda x: x['member_id'], members)
        self.assertIn(self.alt_tenant_id, members)
        # get image as alt user
        self.alt_img_cli.get_image(image)

    @test.attr(type='gate')
    @test.idempotent_id('6a5328a5-80e8-4b82-bd32-6c061f128da9')
    def test_get_shared_images(self):
        image = self._create_image()
        self.client.add_member(self.alt_tenant_id, image)
        share_image = self._create_image()
        self.client.add_member(self.alt_tenant_id, share_image)
        body = self.client.get_shared_images(self.alt_tenant_id)
        images = body['shared_images']
        images = map(lambda x: x['image_id'], images)
        self.assertIn(share_image, images)
        self.assertIn(image, images)

    @test.attr(type='gate')
    @test.idempotent_id('a76a3191-8948-4b44-a9d6-4053e5f2b138')
    def test_remove_member(self):
        image_id = self._create_image()
        self.client.add_member(self.alt_tenant_id, image_id)
        self.client.delete_member(self.alt_tenant_id, image_id)
        body = self.client.get_image_membership(image_id)
        members = body['members']
        self.assertEqual(0, len(members), str(members))
