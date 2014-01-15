# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack Foundation
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

import uuid

from tempest.api.compute import base
from tempest.common.utils import data_utils
from tempest import exceptions
from tempest.test import attr


class VolumesNegativeTest(base.BaseV2ComputeTest):
    _interface = 'json'

    @classmethod
    def setUpClass(cls):
        super(VolumesNegativeTest, cls).setUpClass()
        cls.client = cls.volumes_extensions_client
        if not cls.config.service_available.cinder:
            skip_msg = ("%s skipped as Cinder is not available" % cls.__name__)
            raise cls.skipException(skip_msg)

    @attr(type=['negative', 'gate'])
    def test_volume_get_nonexistent_volume_id(self):
        # Negative: Should not be able to get details of nonexistent volume
        # Creating a nonexistent volume id
        # Trying to GET a non existent volume
        self.assertRaises(exceptions.NotFound, self.client.get_volume,
                          str(uuid.uuid4()))

    @attr(type=['negative', 'gate'])
    def test_volume_delete_nonexistent_volume_id(self):
        # Negative: Should not be able to delete nonexistent Volume
        # Creating nonexistent volume id
        # Trying to DELETE a non existent volume
        self.assertRaises(exceptions.NotFound, self.client.delete_volume,
                          str(uuid.uuid4()))

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_invalid_size(self):
        # Negative: Should not be able to create volume with invalid size
        # in request
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='#$%', display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_out_passing_size(self):
        # Negative: Should not be able to create volume without passing size
        # in request
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='', display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_create_volume_with_size_zero(self):
        # Negative: Should not be able to create volume with size zero
        v_name = data_utils.rand_name('Volume-')
        metadata = {'Type': 'work'}
        self.assertRaises(exceptions.BadRequest, self.client.create_volume,
                          size='0', display_name=v_name, metadata=metadata)

    @attr(type=['negative', 'gate'])
    def test_get_invalid_volume_id(self):
        # Negative: Should not be able to get volume with invalid id
        self.assertRaises(exceptions.NotFound,
                          self.client.get_volume, '#$%%&^&^')

    @attr(type=['negative', 'gate'])
    def test_get_volume_without_passing_volume_id(self):
        # Negative: Should not be able to get volume when empty ID is passed
        self.assertRaises(exceptions.NotFound, self.client.get_volume, '')

    @attr(type=['negative', 'gate'])
    def test_delete_invalid_volume_id(self):
        # Negative: Should not be able to delete volume when invalid ID is
        # passed
        self.assertRaises(exceptions.NotFound,
                          self.client.delete_volume, '!@#$%^&*()')

    @attr(type=['negative', 'gate'])
    def test_delete_volume_without_passing_volume_id(self):
        # Negative: Should not be able to delete volume when empty ID is passed
        self.assertRaises(exceptions.NotFound, self.client.delete_volume, '')


class VolumesNegativeTestXML(VolumesNegativeTest):
    _interface = "xml"
