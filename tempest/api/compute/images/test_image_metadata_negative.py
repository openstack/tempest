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

from tempest.api.compute import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class ImagesMetadataNegativeTestJSON(base.BaseV2ComputeTest):
    """Negative tests of image metadata

    Negative tests of image metadata with compute microversion less than 2.39.
    """

    max_microversion = '2.38'

    @classmethod
    def setup_clients(cls):
        super(ImagesMetadataNegativeTestJSON, cls).setup_clients()
        cls.client = cls.compute_images_client

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('94069db2-792f-4fa8-8bd3-2271a6e0c095')
    def test_list_nonexistent_image_metadata(self):
        """Test listing metadata of a non existence image should fail"""
        self.assertRaises(lib_exc.NotFound, self.client.list_image_metadata,
                          data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a403ef9e-9f95-427c-b70a-3ce3388796f1')
    def test_update_nonexistent_image_metadata(self):
        """Test updating metadata of a non existence image should fail"""
        meta = {'os_distro': 'alt1', 'os_version': 'alt2'}
        self.assertRaises(lib_exc.NotFound,
                          self.client.update_image_metadata,
                          data_utils.rand_uuid(), meta)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('41ae052c-6ee6-405c-985e-5712393a620d')
    def test_get_nonexistent_image_metadata_item(self):
        """Test getting metadata of a non existence image should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.show_image_metadata_item,
                          data_utils.rand_uuid(), 'os_version')

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('dc64f2ce-77e8-45b0-88c8-e15041d08eaf')
    def test_set_nonexistent_image_metadata(self):
        """Test setting metadata of a non existence image should fail"""
        meta = {'os_distro': 'alt1', 'os_version': 'alt2'}
        self.assertRaises(lib_exc.NotFound, self.client.set_image_metadata,
                          data_utils.rand_uuid(), meta)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('2154fd03-ab54-457c-8874-e6e3eb56e9cf')
    def test_set_nonexistent_image_metadata_item(self):
        """Test setting metadata item of a non existence image should fail"""
        meta = {'os_distro': 'alt'}
        self.assertRaises(lib_exc.NotFound,
                          self.client.set_image_metadata_item,
                          data_utils.rand_uuid(), 'os_distro',
                          meta)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('848e157f-6bcf-4b2e-a5dd-5124025a8518')
    def test_delete_nonexistent_image_metadata_item(self):
        """Test deleting metadata item of a non existence image should fail"""
        self.assertRaises(lib_exc.NotFound,
                          self.client.delete_image_metadata_item,
                          data_utils.rand_uuid(), 'os_distro')
