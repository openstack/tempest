# Copyright (C) 2017 Dell Inc. or its subsidiaries.
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


class GroupTypesTest(base.BaseVolumeAdminTest):
    """Test group types"""

    min_microversion = '3.11'
    max_microversion = 'latest'

    @decorators.idempotent_id('dd71e5f9-393e-4d4f-90e9-fa1b8d278864')
    def test_group_type_create_list_update_show(self):
        """Test create/list/update/show group type"""
        name = data_utils.rand_name(self.__class__.__name__ + '-group-type')
        description = data_utils.rand_name("group-type-description")
        group_specs = {"consistent_group_snapshot_enabled": "<is> False"}
        params = {'name': name,
                  'description': description,
                  'group_specs': group_specs,
                  'is_public': True}
        body = self.create_group_type(**params)
        self.assertIn('name', body)
        err_msg = ("The created group_type %(var)s is not equal to the "
                   "requested %(var)s")
        self.assertEqual(name, body['name'], err_msg % {"var": "name"})
        self.assertEqual(description, body['description'],
                         err_msg % {"var": "description"})

        group_list = (
            self.admin_group_types_client.list_group_types()['group_types'])
        self.assertIsInstance(group_list, list)
        self.assertNotEmpty(group_list)

        update_params = {
            'name': data_utils.rand_name(
                self.__class__.__name__ + '-updated-group-type'),
            'description': 'updated-group-type-desc'
        }
        updated_group_type = self.admin_group_types_client.update_group_type(
            body['id'], **update_params)['group_type']
        for key, expected_val in update_params.items():
            self.assertEqual(expected_val, updated_group_type[key])

        fetched_group_type = self.admin_group_types_client.show_group_type(
            body['id'])['group_type']
        params.update(update_params)  # Add updated params to original params.
        for key in params.keys():
            self.assertEqual(params[key], fetched_group_type[key],
                             '%s of the fetched group_type is different '
                             'from the created group_type' % key)
