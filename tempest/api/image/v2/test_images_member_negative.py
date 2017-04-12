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


class ImagesMemberNegativeTest(base.BaseV2MemberImageTest):

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('b79efb37-820d-4cf0-b54c-308b00cf842c')
    def test_image_share_invalid_status(self):
        image_id = self._create_image()
        member = self.image_member_client.create_image_member(
            image_id, member=self.alt_tenant_id)
        self.assertEqual(member['status'], 'pending')
        self.assertRaises(lib_exc.BadRequest,
                          self.alt_image_member_client.update_image_member,
                          image_id, self.alt_tenant_id,
                          status='notavalidstatus')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('27002f74-109e-4a37-acd0-f91cd4597967')
    def test_image_share_owner_cannot_accept(self):
        image_id = self._create_image()
        member = self.image_member_client.create_image_member(
            image_id, member=self.alt_tenant_id)
        self.assertEqual(member['status'], 'pending')
        self.assertNotIn(image_id, self._list_image_ids_as_alt())
        self.assertRaises(lib_exc.Forbidden,
                          self.image_member_client.update_image_member,
                          image_id, self.alt_tenant_id, status='accepted')
        self.assertNotIn(image_id, self._list_image_ids_as_alt())
