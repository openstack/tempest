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

import uuid

from tempest.api.image import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class ImagesTagsNegativeTest(base.BaseV2ImageTest):

    @attr(type=['negative', 'gate'])
    def test_update_tags_for_non_existing_image(self):
        # Update tag with non existing image.
        tag = data_utils.rand_name('tag-')
        non_exist_image = str(uuid.uuid4())
        self.assertRaises(exceptions.NotFound, self.client.add_image_tag,
                          non_exist_image, tag)

    @attr(type=['negative', 'gate'])
    def test_delete_non_existing_tag(self):
        # Delete non existing tag.
        resp, body = self.create_image(container_format='bare',
                                       disk_format='raw',
                                       is_public=True,
                                       )
        image_id = body['id']
        tag = data_utils.rand_name('non-exist-tag-')
        self.addCleanup(self.client.delete_image, image_id)
        self.assertRaises(exceptions.NotFound, self.client.delete_image_tag,
                          image_id, tag)
