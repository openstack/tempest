# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import cStringIO as StringIO

from tempest import clients
from tempest.tests.image import base


class ImageMembersTests(base.BaseV1ImageTest):

    @classmethod
    def setUpClass(cls):
        super(ImageMembersTests, cls).setUpClass()
        admin = clients.AdminManager(interface='json')
        cls.admin_client = admin.identity_client
        cls.tenants = cls._get_tenants()

    @classmethod
    def _get_tenants(cls):
        resp, tenants = cls.admin_client.list_tenants()
        tenants = map(lambda x: x['id'], tenants)
        return tenants

    def _create_image(self):
        image_file = StringIO.StringIO('*' * 1024)
        resp, image = self.create_image(container_format='bare',
                                        disk_format='raw',
                                        is_public=True,
                                        data=image_file)
        self.assertEquals(201, resp.status)
        image_id = image['id']
        return image_id

    def test_add_image_member(self):
        image = self._create_image()
        resp = self.client.add_member(self.tenants[0], image)
        self.assertEquals(204, resp.status)
        resp, body = self.client.get_image_membership(image)
        self.assertEquals(200, resp.status)
        members = body['members']
        members = map(lambda x: x['member_id'], members)
        self.assertIn(self.tenants[0], members)

    def test_get_shared_images(self):
        image = self._create_image()
        resp = self.client.add_member(self.tenants[0], image)
        self.assertEquals(204, resp.status)
        share_image = self._create_image()
        resp = self.client.add_member(self.tenants[0], share_image)
        self.assertEquals(204, resp.status)
        resp, body = self.client.get_shared_images(self.tenants[0])
        self.assertEquals(200, resp.status)
        images = body['shared_images']
        images = map(lambda x: x['image_id'], images)
        self.assertIn(share_image, images)
        self.assertIn(image, images)

    def test_remove_member(self):
        image_id = self._create_image()
        resp = self.client.add_member(self.tenants[0], image_id)
        self.assertEquals(204, resp.status)
        resp = self.client.delete_member(self.tenants[0], image_id)
        self.assertEquals(204, resp.status)
        resp, body = self.client.get_image_membership(image_id)
        self.assertEquals(200, resp.status)
        members = body['members']
        self.assertEquals(0, len(members))
