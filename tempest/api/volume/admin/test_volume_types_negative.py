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

from tempest.api.volume import base
from tempest import exceptions
from tempest.test import attr


class VolumeTypesNegativeTest(base.BaseVolumeV1AdminTest):
    _interface = 'json'

    @attr(type='gate')
    def test_create_with_nonexistent_volume_type(self):
        # Should not be able to create volume with nonexistent volume_type.
        self.assertRaises(exceptions.NotFound,
                          self.volumes_client.create_volume, size=1,
                          display_name=str(uuid.uuid4()),
                          volume_type=str(uuid.uuid4()))

    @attr(type='gate')
    def test_create_with_empty_name(self):
        # Should not be able to create volume type with an empty name.
        self.assertRaises(exceptions.BadRequest,
                          self.client.create_volume_type, '')

    @attr(type='gate')
    def test_get_nonexistent_type_id(self):
        # Should not be able to get volume type with nonexistent type id.
        self.assertRaises(exceptions.NotFound, self.client.get_volume_type,
                          str(uuid.uuid4()))

    @attr(type='gate')
    def test_delete_nonexistent_type_id(self):
        # Should not be able to delete volume type with nonexistent type id.
        self.assertRaises(exceptions.NotFound, self.client.delete_volume_type,
                          str(uuid.uuid4()))


class VolumesTypesNegativeTestXML(VolumeTypesNegativeTest):
    _interface = 'xml'
