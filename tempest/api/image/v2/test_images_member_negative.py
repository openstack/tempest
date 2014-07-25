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
from tempest import exceptions
from tempest import test


class ImagesMemberNegativeTest(base.BaseV2MemberImageTest):
    _interface = 'json'

    @test.attr(type=['negative', 'gate'])
    def test_image_share_invalid_status(self):
        image_id = self._create_image()
        _, member = self.os_img_client.add_member(image_id,
                                                  self.alt_tenant_id)
        self.assertEqual(member['status'], 'pending')
        self.assertRaises(exceptions.BadRequest,
                          self.alt_img_client.update_member_status,
                          image_id, self.alt_tenant_id, 'notavalidstatus')

    @test.attr(type=['negative', 'gate'])
    def test_image_share_owner_cannot_accept(self):
        image_id = self._create_image()
        _, member = self.os_img_client.add_member(image_id,
                                                  self.alt_tenant_id)
        self.assertEqual(member['status'], 'pending')
        self.assertNotIn(image_id, self._list_image_ids_as_alt())
        self.assertRaises(exceptions.Unauthorized,
                          self.os_img_client.update_member_status,
                          image_id, self.alt_tenant_id, 'accepted')
        self.assertNotIn(image_id, self._list_image_ids_as_alt())
