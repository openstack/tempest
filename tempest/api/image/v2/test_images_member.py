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


class ImagesMemberTest(base.BaseV2MemberImageTest):
    _interface = 'json'

    @test.attr(type='gate')
    def test_image_share_accept(self):
        image_id = self._create_image()
        resp, member = self.os_img_client.add_member(image_id,
                                                     self.alt_tenant_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(member['member_id'], self.alt_tenant_id)
        self.assertEqual(member['image_id'], image_id)
        self.assertEqual(member['status'], 'pending')
        self.assertNotIn(image_id, self._list_image_ids_as_alt())
        self.alt_img_client.update_member_status(image_id,
                                                 self.alt_tenant_id,
                                                 'accepted')
        self.assertIn(image_id, self._list_image_ids_as_alt())
        resp, body = self.os_img_client.get_image_membership(image_id)
        self.assertEqual(200, resp.status)
        members = body['members']
        member = members[0]
        self.assertEqual(len(members), 1, str(members))
        self.assertEqual(member['member_id'], self.alt_tenant_id)
        self.assertEqual(member['image_id'], image_id)
        self.assertEqual(member['status'], 'accepted')

    @test.attr(type='gate')
    def test_image_share_reject(self):
        image_id = self._create_image()
        resp, member = self.os_img_client.add_member(image_id,
                                                     self.alt_tenant_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(member['member_id'], self.alt_tenant_id)
        self.assertEqual(member['image_id'], image_id)
        self.assertEqual(member['status'], 'pending')
        self.assertNotIn(image_id, self._list_image_ids_as_alt())
        resp, _ = self.alt_img_client.update_member_status(image_id,
                                                           self.alt_tenant_id,
                                                           'rejected')
        self.assertEqual(200, resp.status)
        self.assertNotIn(image_id, self._list_image_ids_as_alt())

    @test.attr(type='gate')
    def test_get_image_member(self):
        image_id = self._create_image()
        self.os_img_client.add_member(image_id,
                                      self.alt_tenant_id)
        self.alt_img_client.update_member_status(image_id,
                                                 self.alt_tenant_id,
                                                 'accepted')

        self.assertIn(image_id, self._list_image_ids_as_alt())
        resp, member = self.os_img_client.get_member(image_id,
                                                     self.alt_tenant_id)
        self.assertEqual(200, resp.status)
        self.assertEqual(self.alt_tenant_id, member['member_id'])
        self.assertEqual(image_id, member['image_id'])
        self.assertEqual('accepted', member['status'])

    @test.attr(type='gate')
    def test_remove_image_member(self):
        image_id = self._create_image()
        self.os_img_client.add_member(image_id,
                                      self.alt_tenant_id)
        self.alt_img_client.update_member_status(image_id,
                                                 self.alt_tenant_id,
                                                 'accepted')

        self.assertIn(image_id, self._list_image_ids_as_alt())
        resp = self.os_img_client.remove_member(image_id, self.alt_tenant_id)
        self.assertEqual(204, resp.status)
        self.assertNotIn(image_id, self._list_image_ids_as_alt())
