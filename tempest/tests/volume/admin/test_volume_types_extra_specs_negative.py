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

from tempest.common.utils.data_utils import rand_name
from tempest import exceptions
from tempest.tests.volume.admin.base import BaseVolumeAdminTestJSON
from tempest.tests.volume.admin.base import BaseVolumeAdminTestXML


class ExtraSpecsNegativeTestBase():

    @staticmethod
    def setUpClass(cls):
        cls.client = cls.client
        vol_type_name = rand_name('Volume-type-')
        cls.extra_specs = {"spec1": "val1"}
        resp, cls.volume_type = cls.client.create_volume_type(vol_type_name,
                                                              extra_specs=
                                                              cls.extra_specs)

    @staticmethod
    def tearDownClass(cls):
        cls.client.delete_volume_type(cls.volume_type['id'])

    @unittest.skip('Until bug 1090320 is fixed')
    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_update_no_body(self):
        """ Should not update volume type extra specs with no body"""
        extra_spec = {"spec1": "val2"}
        self.client.update_volume_type_extra_specs(self.volume_type['id'],
                                                   extra_spec.keys()[0],
                                                   None)

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_update_nonexistent_extra_spec_id(self):
        """ Should not update volume type extra specs with nonexistent id."""
        extra_spec = {"spec1": "val2"}
        self.client.update_volume_type_extra_specs(self.volume_type['id'],
                                                   str(uuid.uuid4()),
                                                   extra_spec)

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_update_none_extra_spec_id(self):
        """ Should not update volume type extra specs with none id."""
        extra_spec = {"spec1": "val2"}
        self.client.update_volume_type_extra_specs(self.volume_type['id'],
                                                   None, extra_spec)

    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_update_multiple_extra_spec(self):
        """ Should not update volume type extra specs with multiple specs as
            body.
        """
        extra_spec = {"spec1": "val2", 'spec2': 'val1'}
        self.client.update_volume_type_extra_specs(self.volume_type['id'],
                                                   extra_spec.keys()[0],
                                                   extra_spec)

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_create_nonexistent_type_id(self):
        """ Should not create volume type extra spec for nonexistent volume
            type id.
        """
        extra_specs = {"spec2": "val1"}
        self.client.create_volume_type_extra_specs(str(uuid.uuid4()),
                                                   extra_specs)

    @unittest.skip('Until bug 1090322 is fixed')
    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_none_body(self):
        """ Should not create volume type extra spec for none POST body."""
        self.client.create_volume_type_extra_specs(self.volume_type['id'],
                                                   None)

    @unittest.skip('Until bug 1090322 is fixed')
    @raises(exceptions.BadRequest)
    @attr(type='negative')
    def test_create_invalid_body(self):
        """ Should not create volume type extra spec for invalid POST body."""
        self.client.create_volume_type_extra_specs(self.volume_type['id'],
                                                   ['invalid'])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_delete_nonexistent_volume_type_id(self):
        """ Should not delete volume type extra spec for nonexistent
            type id.
        """
        extra_specs = {"spec1": "val1"}
        self.client.delete_volume_type_extra_specs(str(uuid.uuid4()),
                                                   extra_specs.keys()[0])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_list_nonexistent_volume_type_id(self):
        """ Should not list volume type extra spec for nonexistent type id."""
        self.client.list_volume_types_extra_specs(str(uuid.uuid4()))

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_nonexistent_volume_type_id(self):
        """ Should not get volume type extra spec for nonexistent type id."""
        extra_specs = {"spec1": "val1"}
        self.client.get_volume_type_extra_specs(str(uuid.uuid4()),
                                                extra_specs.keys()[0])

    @raises(exceptions.NotFound)
    @attr(type='negative')
    def test_get_nonexistent_extra_spec_id(self):
        """ Should not get volume type extra spec for nonexistent extra spec
            id.
        """
        self.client.get_volume_type_extra_specs(self.volume_type['id'],
                                                str(uuid.uuid4()))


class ExtraSpecsNegativeTestXML(BaseVolumeAdminTestXML,
                                ExtraSpecsNegativeTestBase):

    @classmethod
    def setUpClass(cls):
        super(ExtraSpecsNegativeTestXML, cls).setUpClass()
        ExtraSpecsNegativeTestBase.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        super(ExtraSpecsNegativeTestXML, cls).tearDownClass()
        ExtraSpecsNegativeTestBase.tearDownClass(cls)


class ExtraSpecsNegativeTestJSON(BaseVolumeAdminTestJSON,
                                 ExtraSpecsNegativeTestBase):

    @classmethod
    def setUpClass(cls):
        super(ExtraSpecsNegativeTestJSON, cls).setUpClass()
        ExtraSpecsNegativeTestBase.setUpClass(cls)

    @classmethod
    def tearDownClass(cls):
        super(ExtraSpecsNegativeTestJSON, cls).tearDownClass()
        ExtraSpecsNegativeTestBase.tearDownClass(cls)
