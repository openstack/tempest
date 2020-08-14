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
from tempest.lib import decorators
from tempest.lib import exceptions as lib_exc


class VolumeTypesExtraSpecsTest(base.BaseVolumeAdminTest):
    """Test volume type extra specs"""

    @classmethod
    def resource_setup(cls):
        super(VolumeTypesExtraSpecsTest, cls).resource_setup()
        cls.volume_type = cls.create_volume_type()

    @decorators.idempotent_id('b42923e9-0452-4945-be5b-d362ae533e60')
    def test_volume_type_extra_specs_list(self):
        """Test listing volume type extra specs"""
        extra_specs = {"spec1": "val1"}
        body = self.admin_volume_types_client.create_volume_type_extra_specs(
            self.volume_type['id'], extra_specs)['extra_specs']
        self.assertEqual(extra_specs, body,
                         "Volume type extra spec incorrectly created")
        body = self.admin_volume_types_client.list_volume_types_extra_specs(
            self.volume_type['id'])['extra_specs']
        self.assertIsInstance(body, dict)
        self.assertIn('spec1', body)

    @decorators.idempotent_id('0806db36-b4a0-47a1-b6f3-c2e7f194d017')
    def test_volume_type_extra_specs_update(self):
        """Test updating volume type extra specs"""
        extra_specs = {"spec2": "val1"}
        body = self.admin_volume_types_client.create_volume_type_extra_specs(
            self.volume_type['id'], extra_specs)['extra_specs']
        self.assertEqual(extra_specs, body,
                         "Volume type extra spec incorrectly created")

        # Only update an extra spec
        spec_key = "spec2"
        extra_spec = {spec_key: "val2"}
        body = self.admin_volume_types_client.update_volume_type_extra_specs(
            self.volume_type['id'], spec_key, extra_spec)
        self.assertIn(spec_key, body)
        self.assertEqual(extra_spec[spec_key], body[spec_key])
        body = self.admin_volume_types_client.show_volume_type_extra_specs(
            self.volume_type['id'], spec_key)
        self.assertIn(spec_key, body)
        self.assertEqual(extra_spec[spec_key], body[spec_key],
                         "Volume type extra spec incorrectly updated")

        # Update an existing extra spec and create a new extra spec
        extra_specs = {spec_key: "val3", "spec4": "val4"}
        body = self.admin_volume_types_client.create_volume_type_extra_specs(
            self.volume_type['id'], extra_specs)['extra_specs']
        self.assertEqual(extra_specs, body)
        body = self.admin_volume_types_client.list_volume_types_extra_specs(
            self.volume_type['id'])['extra_specs']
        for key in extra_specs:
            self.assertIn(key, body)
            self.assertEqual(extra_specs[key], body[key],
                             "Volume type extra spec incorrectly created")

    @decorators.idempotent_id('d4772798-601f-408a-b2a5-29e8a59d1220')
    def test_volume_type_extra_spec_create_get_delete(self):
        """Test Create/Get/Delete volume type extra specs"""
        spec_key = "spec3"
        extra_specs = {spec_key: "val1"}
        body = self.admin_volume_types_client.create_volume_type_extra_specs(
            self.volume_type['id'],
            extra_specs)['extra_specs']
        self.assertEqual(extra_specs, body,
                         "Volume type extra spec incorrectly created")

        body = self.admin_volume_types_client.show_volume_type_extra_specs(
            self.volume_type['id'],
            spec_key)
        self.assertEqual(extra_specs, body,
                         "Volume type extra spec incorrectly fetched")

        self.admin_volume_types_client.delete_volume_type_extra_specs(
            self.volume_type['id'], spec_key)
        self.assertRaises(
            lib_exc.NotFound,
            self.admin_volume_types_client.show_volume_type_extra_specs,
            self.volume_type['id'], spec_key)
