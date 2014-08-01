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
    def test_add_image_member(self):
        image = self._create_image()
        self.client.add_member(self.alt_tenant_id, image)
        _, body = self.client.get_image_membership(image)
        members = body['members']
        members = map(lambda x: x['member_id'], members)
        self.assertIn(self.alt_tenant_id, members)
        # get image as alt user
        self.alt_img_cli.get_image(image)

    @test.attr(type='gate')
    def test_get_shared_images(self):
        image = self._create_image()
        self.client.add_member(self.alt_tenant_id, image)
        share_image = self._create_image()
        self.client.add_member(self.alt_tenant_id, share_image)
        _, body = self.client.get_shared_images(self.alt_tenant_id)
        images = body['shared_images']
        images = map(lambda x: x['image_id'], images)
        self.assertIn(share_image, images)
        self.assertIn(image, images)

    @test.attr(type='gate')
    def test_remove_member(self):
        image_id = self._create_image()
        self.client.add_member(self.alt_tenant_id, image_id)
        self.client.delete_member(self.alt_tenant_id, image_id)
        _, body = self.client.get_image_membership(image_id)
        members = body['members']
        self.assertEqual(0, len(members), str(members))

    @test.attr(type='gate')
    def test_set_membership(self):
        image_id = self._create_image()

        membership = {
            "memberships": [{
                            "can_share": True,
                            "member_id": self.client.tenant_id
                            },
                            {
                            "can_share": False,
                            "member_id": self.alt_tenant_id
                            }]
            }
        self.client.set_image_membership(image_id, membership)

        _, body = self.client.get_image_membership(image_id)
        members = body
        members['memberships'] = body.pop('members')
        self.assertEqual(membership, members, str(body))
