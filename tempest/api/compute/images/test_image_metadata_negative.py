# Copyright 2013 OpenStack Foundation
# All Rights Reserved.
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

from tempest_lib.common.utils import data_utils
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest import test


class ImagesMetadataTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def setup_clients(cls):
        super(ImagesMetadataTestJSON, cls).setup_clients()
        cls.client = cls.images_client

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('94069db2-792f-4fa8-8bd3-2271a6e0c095')
    def test_list_nonexistent_image_metadata(self):
        # Negative test: List on nonexistent image
        # metadata should not happen
        self.assertRaises(lib_exc.NotFound, self.client.list_image_metadata,
                          data_utils.rand_uuid())

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('a403ef9e-9f95-427c-b70a-3ce3388796f1')
    def test_update_nonexistent_image_metadata(self):
        # Negative test:An update should not happen for a non-existent image
        meta = {'os_distro': 'alt1', 'os_version': 'alt2'}
        self.assertRaises(lib_exc.NotFound,
                          self.client.update_image_metadata,
                          data_utils.rand_uuid(), meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('41ae052c-6ee6-405c-985e-5712393a620d')
    def test_get_nonexistent_image_metadata_item(self):
        # Negative test: Get on non-existent image should not happen
        self.assertRaises(lib_exc.NotFound,
                          self.client.get_image_metadata_item,
                          data_utils.rand_uuid(), 'os_version')

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('dc64f2ce-77e8-45b0-88c8-e15041d08eaf')
    def test_set_nonexistent_image_metadata(self):
        # Negative test: Metadata should not be set to a non-existent image
        meta = {'os_distro': 'alt1', 'os_version': 'alt2'}
        self.assertRaises(lib_exc.NotFound, self.client.set_image_metadata,
                          data_utils.rand_uuid(), meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('2154fd03-ab54-457c-8874-e6e3eb56e9cf')
    def test_set_nonexistent_image_metadata_item(self):
        # Negative test: Metadata item should not be set to a
        # nonexistent image
        meta = {'os_distro': 'alt'}
        self.assertRaises(lib_exc.NotFound,
                          self.client.set_image_metadata_item,
                          data_utils.rand_uuid(), 'os_distro',
                          meta)

    @test.attr(type=['negative', 'gate'])
    @test.idempotent_id('848e157f-6bcf-4b2e-a5dd-5124025a8518')
    def test_delete_nonexistent_image_metadata_item(self):
        # Negative test: Shouldn't be able to delete metadata
        # item from non-existent image
        self.assertRaises(lib_exc.NotFound,
                          self.client.delete_image_metadata_item,
                          data_utils.rand_uuid(), 'os_distro')
