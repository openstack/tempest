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
from tempest.lib import exceptions as lib_exc


class ImagesTagsNegativeTest(base.BaseV2ImageTest):
    """Negative tests of image tags"""

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('8cd30f82-6f9a-4c6e-8034-c1b51fba43d9')
    def test_update_tags_for_non_existing_image(self):
        """Update image tag with non existing image"""
        tag = data_utils.rand_name('tag')
        non_exist_image = data_utils.rand_uuid()
        self.assertRaises(lib_exc.NotFound, self.client.add_image_tag,
                          non_exist_image, tag)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('39c023a2-325a-433a-9eea-649bf1414b19')
    def test_delete_non_existing_tag(self):
        """Delete non existing image tag"""
        image = self.create_image(container_format='bare',
                                  disk_format='raw',
                                  visibility='private'
                                  )
        tag = data_utils.rand_name('non-exist-tag')
        self.addCleanup(self.client.delete_image, image['id'])
        self.assertRaises(lib_exc.NotFound, self.client.delete_image_tag,
                          image['id'], tag)
