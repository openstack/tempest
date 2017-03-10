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
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators


class ImagesTagsTest(base.BaseV2ImageTest):

    @decorators.idempotent_id('10407036-6059-4f95-a2cd-cbbbee7ed329')
    def test_update_delete_tags_for_image(self):
        image = self.create_image(container_format='bare',
                                  disk_format='raw',
                                  visibility='private')
        tag = data_utils.rand_name('tag')
        self.addCleanup(self.client.delete_image, image['id'])

        # Creating image tag and verify it.
        self.client.add_image_tag(image['id'], tag)
        body = self.client.show_image(image['id'])
        self.assertIn(tag, body['tags'])

        # Deleting image tag and verify it.
        self.client.delete_image_tag(image['id'], tag)
        body = self.client.show_image(image['id'])
        self.assertNotIn(tag, body['tags'])
