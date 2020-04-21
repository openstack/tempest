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


class ImagesMemberTest(base.BaseV2MemberImageTest):
    """Test image members"""

    @decorators.idempotent_id('5934c6ea-27dc-4d6e-9421-eeb5e045494a')
    def test_image_share_accept(self):
        """Test sharing and accepting an image"""
        image_id = self._create_image()
        member = self.image_member_client.create_image_member(
            image_id, member=self.alt_tenant_id)
        self.addCleanup(self.image_member_client.delete_image_member,
                        image_id, self.alt_tenant_id)
        self.assertEqual(member['member_id'], self.alt_tenant_id)
        self.assertEqual(member['image_id'], image_id)
        self.assertEqual(member['status'], 'pending')
        self.assertNotIn(image_id, self._list_image_ids_as_alt())
        self.alt_image_member_client.update_image_member(image_id,
                                                         self.alt_tenant_id,
                                                         status='accepted')
        self.assertIn(image_id, self._list_image_ids_as_alt())
        body = self.image_member_client.list_image_members(image_id)
        members = body['members']
        self.assertEqual(len(members), 1, str(members))
        member = members[0]
        self.assertEqual(member['member_id'], self.alt_tenant_id)
        self.assertEqual(member['image_id'], image_id)
        self.assertEqual(member['status'], 'accepted')

    @decorators.idempotent_id('d9e83e5f-3524-4b38-a900-22abcb26e90e')
    def test_image_share_reject(self):
        """Test sharing and rejecting an image"""
        image_id = self._create_image()
        member = self.image_member_client.create_image_member(
            image_id, member=self.alt_tenant_id)
        self.addCleanup(self.image_member_client.delete_image_member,
                        image_id, self.alt_tenant_id)
        self.assertEqual(member['member_id'], self.alt_tenant_id)
        self.assertEqual(member['image_id'], image_id)
        self.assertEqual(member['status'], 'pending')
        self.assertNotIn(image_id, self._list_image_ids_as_alt())
        self.alt_image_member_client.update_image_member(image_id,
                                                         self.alt_tenant_id,
                                                         status='rejected')
        self.assertNotIn(image_id, self._list_image_ids_as_alt())

    @decorators.idempotent_id('a6ee18b9-4378-465e-9ad9-9a6de58a3287')
    def test_get_image_member(self):
        """Test getting image members after the image is accepted"""
        image_id = self._create_image()
        self.image_member_client.create_image_member(
            image_id, member=self.alt_tenant_id)
        self.addCleanup(self.image_member_client.delete_image_member,
                        image_id, self.alt_tenant_id)
        self.alt_image_member_client.update_image_member(image_id,
                                                         self.alt_tenant_id,
                                                         status='accepted')

        self.assertIn(image_id, self._list_image_ids_as_alt())
        member = self.image_member_client.show_image_member(
            image_id, self.alt_tenant_id)
        self.assertEqual(self.alt_tenant_id, member['member_id'])
        self.assertEqual(image_id, member['image_id'])
        self.assertEqual('accepted', member['status'])

    @decorators.idempotent_id('72989bc7-2268-48ed-af22-8821e835c914')
    def test_remove_image_member(self):
        """Test removing image members after the image is accepted"""
        image_id = self._create_image()
        self.image_member_client.create_image_member(
            image_id, member=self.alt_tenant_id)
        self.alt_image_member_client.update_image_member(image_id,
                                                         self.alt_tenant_id,
                                                         status='accepted')

        self.assertIn(image_id, self._list_image_ids_as_alt())
        self.image_member_client.delete_image_member(image_id,
                                                     self.alt_tenant_id)
        self.assertNotIn(image_id, self._list_image_ids_as_alt())

    @decorators.idempotent_id('634dcc3f-f6e2-4409-b8fd-354a0bb25d83')
    def test_get_image_member_schema(self):
        """Test getting image member schema"""
        body = self.schemas_client.show_schema("member")
        self.assertEqual("member", body['name'])

    @decorators.idempotent_id('6ae916ef-1052-4e11-8d36-b3ae14853cbb')
    def test_get_image_members_schema(self):
        """Test getting image members schema"""
        body = self.schemas_client.show_schema("members")
        self.assertEqual("members", body['name'])
