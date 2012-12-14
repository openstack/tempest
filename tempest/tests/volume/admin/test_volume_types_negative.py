# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 OpenStack, LLC
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

import unittest
import uuid

from nose.plugins.attrib import attr
from nose.tools import raises

from tempest import exceptions
from tempest.tests.volume.admin.base import BaseVolumeAdminTestJSON
from tempest.tests.volume.admin.base import BaseVolumeAdminTestXML


class VolumeTypesNegativeTestBase():

    @staticmethod
    def setUpClass(cls):
        cls.client = cls.client

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_create_with_nonexistent_volume_type(self):
        """ Should not be able to create volume with nonexistent volume_type.
        """
        self.volumes_client.create_volume(size=1,
                                          display_name=str(uuid.uuid4()),
                                          volume_type=str(uuid.uuid4()))

    @unittest.skip('Until bug 1090356 is fixed')
    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_with_empty_name(self):
        """ Should not be able to create volume type with an empty name."""
        self.client.create_volume_type('')

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_nonexistent_type_id(self):
        """ Should not be able to get volume type with nonexistent type id."""
        self.client.get_volume_type(str(uuid.uuid4()))

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_nonexistent_type_id(self):
        """ Should not be able to delete volume type with nonexistent type id.
        """
        self.client.delete_volume_type(str(uuid.uuid4()))


class VolumesTypesNegativeTestXML(BaseVolumeAdminTestXML,
                                  VolumeTypesNegativeTestBase):
    @classmethod
    def setUpClass(cls):
        super(VolumesTypesNegativeTestXML, cls).setUpClass()
        VolumeTypesNegativeTestBase.setUpClass(cls)


class VolumesTypesNegativeTestJSON(BaseVolumeAdminTestJSON,
                                   VolumeTypesNegativeTestBase):
    @classmethod
    def setUpClass(cls):
        super(VolumesTypesNegativeTestJSON, cls).setUpClass()
        VolumeTypesNegativeTestBase.setUpClass(cls)
