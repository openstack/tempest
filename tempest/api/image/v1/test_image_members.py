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
from tempest.test import attr


class ImageMembersTest(base.BaseV1ImageMembersTest):

    @attr(type='gate')
    def test_add_image_member(self):
        image = self._create_image()
        resp = self.client.add_member(self.alt_tenant_id, image)
        self.assertEqual(204, resp.status)
        resp, body = self.client.get_image_membership(image)
        self.assertEqual(200, resp.status)
        members = body['members']
        members = map(lambda x: x['member_id'], members)
        self.assertIn(self.alt_tenant_id, members)
        # get image as alt user
        resp, body = self.alt_img_cli.get_image(image)
        self.assertEqual(200, resp.status)

    @attr(type='gate')
    def test_get_shared_images(self):
        image = self._create_image()
        resp = self.client.add_member(self.alt_tenant_id, image)
        self.assertEqual(204, resp.status)
        share_image = self._create_image()
        resp = self.client.add_member(self.alt_tenant_id, share_image)
        self.assertEqual(204, resp.status)
        resp, body = self.client.get_shared_images(self.alt_tenant_id)
        self.assertEqual(200, resp.status)
        images = body['shared_images']
        images = map(lambda x: x['image_id'], images)
        self.assertIn(share_image, images)
        self.assertIn(image, images)

    @attr(type='gate')
    def test_remove_member(self):
        image_id = self._create_image()
        resp = self.client.add_member(self.alt_tenant_id, image_id)
        self.assertEqual(204, resp.status)
        resp = self.client.delete_member(self.alt_tenant_id, image_id)
        self.assertEqual(204, resp.status)
        resp, body = self.client.get_image_membership(image_id)
        self.assertEqual(200, resp.status)
        members = body['members']
        self.assertEqual(0, len(members), str(members))
