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

from tempest_lib.common.utils import data_utils

from tempest.api.volume import base
from tempest import test


class VolumeTypesExtraSpecsV2Test(base.BaseVolumeAdminTest):

    @classmethod
    def resource_setup(cls):
        super(VolumeTypesExtraSpecsV2Test, cls).resource_setup()
        vol_type_name = data_utils.rand_name('Volume-type')
        cls.volume_type = cls.volume_types_client.create_volume_type(
            vol_type_name)

    @classmethod
    def resource_cleanup(cls):
        cls.volume_types_client.delete_volume_type(cls.volume_type['id'])
        super(VolumeTypesExtraSpecsV2Test, cls).resource_cleanup()

    @test.attr(type='smoke')
    @test.idempotent_id('b42923e9-0452-4945-be5b-d362ae533e60')
    def test_volume_type_extra_specs_list(self):
        # List Volume types extra specs.
        extra_specs = {"spec1": "val1"}
        body = self.volume_types_client.create_volume_type_extra_specs(
            self.volume_type['id'], extra_specs)
        self.assertEqual(extra_specs, body,
                         "Volume type extra spec incorrectly created")
        body = self.volume_types_client.list_volume_types_extra_specs(
            self.volume_type['id'])
        self.assertIsInstance(body, dict)
        self.assertIn('spec1', body)

    @test.attr(type='gate')
    @test.idempotent_id('0806db36-b4a0-47a1-b6f3-c2e7f194d017')
    def test_volume_type_extra_specs_update(self):
        # Update volume type extra specs
        extra_specs = {"spec2": "val1"}
        body = self.volume_types_client.create_volume_type_extra_specs(
            self.volume_type['id'], extra_specs)
        self.assertEqual(extra_specs, body,
                         "Volume type extra spec incorrectly created")

        extra_spec = {"spec2": "val2"}
        body = self.volume_types_client.update_volume_type_extra_specs(
            self.volume_type['id'],
            extra_spec.keys()[0],
            extra_spec)
        self.assertIn('spec2', body)
        self.assertEqual(extra_spec['spec2'], body['spec2'],
                         "Volume type extra spec incorrectly updated")

    @test.attr(type='smoke')
    @test.idempotent_id('d4772798-601f-408a-b2a5-29e8a59d1220')
    def test_volume_type_extra_spec_create_get_delete(self):
        # Create/Get/Delete volume type extra spec.
        extra_specs = {"spec3": "val1"}
        body = self.volume_types_client.create_volume_type_extra_specs(
            self.volume_type['id'],
            extra_specs)
        self.assertEqual(extra_specs, body,
                         "Volume type extra spec incorrectly created")

        self.volume_types_client.show_volume_type_extra_specs(
            self.volume_type['id'],
            extra_specs.keys()[0])
        self.assertEqual(extra_specs, body,
                         "Volume type extra spec incorrectly fetched")

        self.volume_types_client.delete_volume_type_extra_specs(
            self.volume_type['id'],
            extra_specs.keys()[0])


class VolumeTypesExtraSpecsV1Test(VolumeTypesExtraSpecsV2Test):
    _api_version = 1
