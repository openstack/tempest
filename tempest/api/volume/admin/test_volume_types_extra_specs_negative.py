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

from tempest.api.volume import base
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class ExtraSpecsNegativeTest(base.BaseVolumeAdminTest):
    """Negative tests of volume type extra specs"""

    @classmethod
    def resource_setup(cls):
        super(ExtraSpecsNegativeTest, cls).resource_setup()
        extra_specs = {"spec1": "val1"}
        cls.volume_type = cls.create_volume_type(extra_specs=extra_specs)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('08961d20-5cbb-4910-ac0f-89ad6dbb2da1')
    def test_update_no_body(self):
        """Test updating volume type extra specs with no body should fail"""
        self.assertRaises(
            lib_exc.BadRequest,
            self.admin_volume_types_client.update_volume_type_extra_specs,
            self.volume_type['id'], "spec1", None)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('25e5a0ee-89b3-4c53-8310-236f76c75365')
    def test_update_nonexistent_extra_spec_id(self):
        """Test updating volume type extra specs with non existent name

        Updating volume type extra specs with non existent extra spec name
        should fail.
        """
        extra_spec = {"spec1": "val2"}
        self.assertRaises(
            lib_exc.BadRequest,
            self.admin_volume_types_client.update_volume_type_extra_specs,
            self.volume_type['id'], data_utils.rand_uuid(),
            extra_spec)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9bf7a657-b011-4aec-866d-81c496fbe5c8')
    def test_update_none_extra_spec_id(self):
        """Test updating volume type extra specs without name

        Updating volume type extra specs without extra spec name should fail.
        """
        extra_spec = {"spec1": "val2"}
        self.assertRaises(
            lib_exc.BadRequest,
            self.admin_volume_types_client.update_volume_type_extra_specs,
            self.volume_type['id'], None, extra_spec)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('a77dfda2-9100-448e-9076-ed1711f4bdfc')
    def test_update_multiple_extra_spec(self):
        """Test updating multiple volume type extra specs should fail"""
        extra_spec = {"spec1": "val2", "spec2": "val1"}
        self.assertRaises(
            lib_exc.BadRequest,
            self.admin_volume_types_client.update_volume_type_extra_specs,
            self.volume_type['id'], list(extra_spec)[0],
            extra_spec)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('49d5472c-a53d-4eab-a4d3-450c4db1c545')
    def test_create_nonexistent_type_id(self):
        """Test creating volume type extra specs for non existent volume type

        Creating volume type extra specs for non existent volume type should
        fail.
        """
        extra_specs = {"spec2": "val1"}
        self.assertRaises(
            lib_exc.NotFound,
            self.admin_volume_types_client.create_volume_type_extra_specs,
            data_utils.rand_uuid(), extra_specs)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c821bdc8-43a4-4bf4-86c8-82f3858d5f7d')
    def test_create_none_body(self):
        """Test creating volume type extra spec with none POST body

        Creating volume type extra spec with none POST body should fail.
        """
        self.assertRaises(
            lib_exc.BadRequest,
            self.admin_volume_types_client.create_volume_type_extra_specs,
            self.volume_type['id'], None)

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('bc772c71-1ed4-4716-b945-8b5ed0f15e87')
    def test_create_invalid_body(self):
        """Test creating volume type extra spec with invalid POST body

        Creating volume type extra spec with invalid POST body should fail.
        """
        self.assertRaises(
            lib_exc.BadRequest,
            self.admin_volume_types_client.create_volume_type_extra_specs,
            self.volume_type['id'], extra_specs=['invalid'])

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('031cda8b-7d23-4246-8bf6-bbe73fd67074')
    def test_delete_nonexistent_volume_type_id(self):
        """Test deleting volume type extra spec for non existent volume type

        Deleting volume type extra spec for non existent volume type should
        fail.
        """
        self.assertRaises(
            lib_exc.NotFound,
            self.admin_volume_types_client.delete_volume_type_extra_specs,
            data_utils.rand_uuid(), "spec1")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('dee5cf0c-cdd6-4353-b70c-e847050d71fb')
    def test_list_nonexistent_volume_type_id(self):
        """Test listing volume type extra spec for non existent volume type

        Listing volume type extra spec for non existent volume type should
        fail.
        """
        self.assertRaises(
            lib_exc.NotFound,
            self.admin_volume_types_client.list_volume_types_extra_specs,
            data_utils.rand_uuid())

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('9f402cbd-1838-4eb4-9554-126a6b1908c9')
    def test_get_nonexistent_volume_type_id(self):
        """Test getting volume type extra spec for non existent volume type

        Getting volume type extra spec for non existent volume type should
        fail.
        """
        self.assertRaises(
            lib_exc.NotFound,
            self.admin_volume_types_client.show_volume_type_extra_specs,
            data_utils.rand_uuid(), "spec1")

    @decorators.attr(type=['negative'])
    @decorators.idempotent_id('c881797d-12ff-4f1a-b09d-9f6212159753')
    def test_get_nonexistent_extra_spec_name(self):
        """Test getting volume type extra spec for non existent spec name

        Getting volume type extra spec for non existent extra spec name should
        fail.
        """
        self.assertRaises(
            lib_exc.NotFound,
            self.admin_volume_types_client.show_volume_type_extra_specs,
            self.volume_type['id'], "nonexistent_extra_spec_name")
