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

from tempest_lib import exceptions as lib_exc

from tempest.api.volume import base
from tempest.common.utils import data_utils
from tempest import test


class ExtraSpecsNegativeV2Test(base.BaseVolumeAdminTest):

    @classmethod
    def resource_setup(cls):
        super(ExtraSpecsNegativeV2Test, cls).resource_setup()
        vol_type_name = data_utils.rand_name('Volume-type-')
        cls.extra_specs = {"spec1": "val1"}
        cls.volume_type = cls.volume_types_client.create_volume_type(
            vol_type_name,
            extra_specs=cls.extra_specs)

    @classmethod
    def resource_cleanup(cls):
        cls.volume_types_client.delete_volume_type(cls.volume_type['id'])
        super(ExtraSpecsNegativeV2Test, cls).resource_cleanup()

    @test.attr(type='gate')
    def test_update_no_body(self):
        # Should not update volume type extra specs with no body
        extra_spec = {"spec1": "val2"}
        self.assertRaises(
            lib_exc.BadRequest,
            self.volume_types_client.update_volume_type_extra_specs,
            self.volume_type['id'], extra_spec.keys()[0], None)

    @test.attr(type='gate')
    def test_update_nonexistent_extra_spec_id(self):
        # Should not update volume type extra specs with nonexistent id.
        extra_spec = {"spec1": "val2"}
        self.assertRaises(
            lib_exc.BadRequest,
            self.volume_types_client.update_volume_type_extra_specs,
            self.volume_type['id'], str(uuid.uuid4()),
            extra_spec)

    @test.attr(type='gate')
    def test_update_none_extra_spec_id(self):
        # Should not update volume type extra specs with none id.
        extra_spec = {"spec1": "val2"}
        self.assertRaises(
            lib_exc.BadRequest,
            self.volume_types_client.update_volume_type_extra_specs,
            self.volume_type['id'], None, extra_spec)

    @test.attr(type='gate')
    def test_update_multiple_extra_spec(self):
        # Should not update volume type extra specs with multiple specs as
            # body.
        extra_spec = {"spec1": "val2", 'spec2': 'val1'}
        self.assertRaises(
            lib_exc.BadRequest,
            self.volume_types_client.update_volume_type_extra_specs,
            self.volume_type['id'], extra_spec.keys()[0],
            extra_spec)

    @test.attr(type='gate')
    def test_create_nonexistent_type_id(self):
        # Should not create volume type extra spec for nonexistent volume
            # type id.
        extra_specs = {"spec2": "val1"}
        self.assertRaises(
            lib_exc.NotFound,
            self.volume_types_client.create_volume_type_extra_specs,
            str(uuid.uuid4()), extra_specs)

    @test.attr(type='gate')
    def test_create_none_body(self):
        # Should not create volume type extra spec for none POST body.
        self.assertRaises(
            lib_exc.BadRequest,
            self.volume_types_client.create_volume_type_extra_specs,
            self.volume_type['id'], None)

    @test.attr(type='gate')
    def test_create_invalid_body(self):
        # Should not create volume type extra spec for invalid POST body.
        self.assertRaises(
            lib_exc.BadRequest,
            self.volume_types_client.create_volume_type_extra_specs,
            self.volume_type['id'], ['invalid'])

    @test.attr(type='gate')
    def test_delete_nonexistent_volume_type_id(self):
        # Should not delete volume type extra spec for nonexistent
            # type id.
        extra_specs = {"spec1": "val1"}
        self.assertRaises(
            lib_exc.NotFound,
            self.volume_types_client.delete_volume_type_extra_specs,
            str(uuid.uuid4()), extra_specs.keys()[0])

    @test.attr(type='gate')
    def test_list_nonexistent_volume_type_id(self):
        # Should not list volume type extra spec for nonexistent type id.
        self.assertRaises(
            lib_exc.NotFound,
            self.volume_types_client.list_volume_types_extra_specs,
            str(uuid.uuid4()))

    @test.attr(type='gate')
    def test_get_nonexistent_volume_type_id(self):
        # Should not get volume type extra spec for nonexistent type id.
        extra_specs = {"spec1": "val1"}
        self.assertRaises(
            lib_exc.NotFound,
            self.volume_types_client.get_volume_type_extra_specs,
            str(uuid.uuid4()), extra_specs.keys()[0])

    @test.attr(type='gate')
    def test_get_nonexistent_extra_spec_id(self):
        # Should not get volume type extra spec for nonexistent extra spec
            # id.
        self.assertRaises(
            lib_exc.NotFound,
            self.volume_types_client.get_volume_type_extra_specs,
            self.volume_type['id'], str(uuid.uuid4()))


class ExtraSpecsNegativeV1Test(ExtraSpecsNegativeV2Test):
    _api_version = 1
