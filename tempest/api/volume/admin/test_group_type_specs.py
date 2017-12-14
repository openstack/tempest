# Copyright 2017 FiberHome Telecommunication Technologies CO.,LTD
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


class GroupTypeSpecsTest(base.BaseVolumeAdminTest):
    _api_version = 3
    min_microversion = '3.11'
    max_microversion = 'latest'

    @decorators.idempotent_id('bb4e30d0-de6e-4f4d-866c-dcc48d023b4e')
    def test_group_type_specs_create_show_update_list_delete(self):
        # Create new group type
        group_type = self.create_group_type()

        # Create new group type specs
        create_specs = {
            "key1": "value1",
            "key2": "value2"
        }
        body = self.admin_group_types_client.create_or_update_group_type_specs(
            group_type['id'], create_specs)['group_specs']
        self.assertEqual(create_specs, body)

        # Create a new group type spec and update an existing group type spec
        update_specs = {
            "key2": "value2-updated",
            "key3": "value3"
        }
        body = self.admin_group_types_client.create_or_update_group_type_specs(
            group_type['id'], update_specs)['group_specs']
        self.assertEqual(update_specs, body)

        # Show specified item of group type specs
        spec_keys = ['key2', 'key3']
        for key in spec_keys:
            body = self.admin_group_types_client.show_group_type_specs_item(
                group_type['id'], key)
            self.assertIn(key, body)
            self.assertEqual(update_specs[key], body[key])

        # Update specified item of group type specs
        update_key = 'key3'
        update_spec = {update_key: "value3-updated"}
        body = self.admin_group_types_client.update_group_type_specs_item(
            group_type['id'], update_key, update_spec)
        self.assertEqual(update_spec, body)

        # List all group type specs that created or updated above
        list_specs = {}
        list_specs.update(create_specs)
        list_specs.update(update_specs)
        list_specs.update(update_spec)
        body = self.admin_group_types_client.list_group_type_specs(
            group_type['id'])['group_specs']
        self.assertEqual(list_specs, body)

        # Delete specified item of group type specs
        delete_key = 'key1'
        self.admin_group_types_client.delete_group_type_specs_item(
            group_type['id'], delete_key)
        self.assertRaises(
            lib_exc.NotFound,
            self.admin_group_types_client.show_group_type_specs_item,
            group_type['id'], delete_key)
