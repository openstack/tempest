# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class ImagesMetadataTestJSON(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(ImagesMetadataTestJSON, cls).setUpClass()
        cls.client = cls.images_client

    @attr(type=['negative', 'gate'])
    def test_list_nonexistent_image_metadata(self):
        # Negative test: List on nonexistent image
        # metadata should not happen
        self.assertRaises(exceptions.NotFound, self.client.list_image_metadata,
                          data_utils.rand_uuid())

    @attr(type=['negative', 'gate'])
    def test_update_nonexistent_image_metadata(self):
        # Negative test:An update should not happen for a non-existent image
        meta = {'key1': 'alt1', 'key2': 'alt2'}
        self.assertRaises(exceptions.NotFound,
                          self.client.update_image_metadata,
                          data_utils.rand_uuid(), meta)

    @attr(type=['negative', 'gate'])
    def test_get_nonexistent_image_metadata_item(self):
        # Negative test: Get on non-existent image should not happen
        self.assertRaises(exceptions.NotFound,
                          self.client.get_image_metadata_item,
                          data_utils.rand_uuid(), 'key2')

    @attr(type=['negative', 'gate'])
    def test_set_nonexistent_image_metadata(self):
        # Negative test: Metadata should not be set to a non-existent image
        meta = {'key1': 'alt1', 'key2': 'alt2'}
        self.assertRaises(exceptions.NotFound, self.client.set_image_metadata,
                          data_utils.rand_uuid(), meta)

    @attr(type=['negative', 'gate'])
    def test_set_nonexistent_image_metadata_item(self):
        # Negative test: Metadata item should not be set to a
        # nonexistent image
        meta = {'key1': 'alt'}
        self.assertRaises(exceptions.NotFound,
                          self.client.set_image_metadata_item,
                          data_utils.rand_uuid(), 'key1',
                          meta)

    @attr(type=['negative', 'gate'])
    def test_delete_nonexistent_image_metadata_item(self):
        # Negative test: Shouldn't be able to delete metadata
        # item from non-existent image
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_image_metadata_item,
                          data_utils.rand_uuid(), 'key1')


class ImagesMetadataTestXML(ImagesMetadataTestJSON):
    _interface = 'xml'
