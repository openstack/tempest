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

from tempest.api.image import base
from tempest import clients
from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.test import attr


class ImageMembersTests(base.BaseV1ImageTest):

    @classmethod
    def setUpClass(cls):
        super(ImageMembersTests, cls).setUpClass()
        if cls.config.compute.allow_tenant_isolation:
            creds = cls.isolated_creds.get_alt_creds()
            username, tenant_name, password = creds
            cls.os_alt = clients.Manager(username=username,
                                         password=password,
                                         tenant_name=tenant_name)
        else:
            cls.os_alt = clients.AltManager()

        alt_tenant_name = cls.os_alt.tenant_name
        identity_client = cls._get_identity_admin_client()
        _, tenants = identity_client.list_tenants()
        cls.alt_tenant_id = [tnt['id'] for tnt in tenants if tnt['name'] ==
                             alt_tenant_name][0]

    def _create_image(self):
        image_file = StringIO.StringIO('*' * 1024)
        resp, image = self.create_image(container_format='bare',
                                        disk_format='raw',
                                        is_public=False,
                                        data=image_file)
        self.assertEqual(201, resp.status)
        image_id = image['id']
        return image_id

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

    @attr(type=['negative', 'gate'])
    def test_add_member_with_non_existing_image(self):
        # Add member with non existing image.
        non_exist_image = rand_name('image_')
        self.assertRaises(exceptions.NotFound, self.client.add_member,
                          self.alt_tenant_id, non_exist_image)

    @attr(type=['negative', 'gate'])
    def test_delete_member_with_non_existing_image(self):
        # Delete member with non existing image.
        non_exist_image = rand_name('image_')
        self.assertRaises(exceptions.NotFound, self.client.delete_member,
                          self.alt_tenant_id, non_exist_image)

    @attr(type=['negative', 'gate'])
    def test_delete_member_with_non_existing_tenant(self):
        # Delete member with non existing tenant.
        image_id = self._create_image()
        non_exist_tenant = rand_name('tenant_')
        self.assertRaises(exceptions.NotFound, self.client.delete_member,
                          non_exist_tenant, image_id)
