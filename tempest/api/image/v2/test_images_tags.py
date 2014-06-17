# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from tempest.api.image import base
from tempest.common.utils import data_utils
from tempest import test


class ImagesTagsTest(base.BaseV2ImageTest):

    @test.attr(type='gate')
    def test_update_delete_tags_for_image(self):
        resp, body = self.create_image(container_format='bare',
                                       disk_format='raw',
                                       visibility='private')
        image_id = body['id']
        tag = data_utils.rand_name('tag-')
        self.addCleanup(self.client.delete_image, image_id)

        # Creating image tag and verify it.
        resp, body = self.client.add_image_tag(image_id, tag)
        self.assertEqual(resp.status, 204)
        resp, body = self.client.get_image(image_id)
        self.assertEqual(resp.status, 200)
        self.assertIn(tag, body['tags'])

        # Deleting image tag and verify it.
        resp = self.client.delete_image_tag(image_id, tag)
        self.assertEqual(resp.status, 204)
        resp, body = self.client.get_image(image_id)
        self.assertEqual(resp.status, 200)
        self.assertNotIn(tag, body['tags'])
