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
from tempest.common import waiters
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators

CONF = config.CONF


class GroupsTest(base.BaseVolumeAdminTest):
    _api_version = 3
    min_microversion = '3.14'
    max_microversion = 'latest'

    def _delete_group(self, grp_id, delete_volumes=True):
        self.admin_groups_client.delete_group(grp_id, delete_volumes)
        vols = self.admin_volume_client.list_volumes(detail=True)['volumes']
        for vol in vols:
            if vol['group_id'] == grp_id:
                self.admin_volume_client.wait_for_resource_deletion(vol['id'])
        self.admin_groups_client.wait_for_resource_deletion(grp_id)

    @decorators.idempotent_id('4b111d28-b73d-4908-9bd2-03dc2992e4d4')
    def test_group_create_show_list_delete(self):
        # Create volume type
        volume_type = self.create_volume_type()

        # Create group type
        group_type = self.create_group_type()

        # Create group
        grp1_name = data_utils.rand_name('Group1')
        grp1 = self.admin_groups_client.create_group(
            group_type=group_type['id'],
            volume_types=[volume_type['id']],
            name=grp1_name)['group']
        waiters.wait_for_volume_resource_status(
            self.admin_groups_client, grp1['id'], 'available')
        grp1_id = grp1['id']

        grp2_name = data_utils.rand_name('Group2')
        grp2 = self.admin_groups_client.create_group(
            group_type=group_type['id'],
            volume_types=[volume_type['id']],
            name=grp2_name)['group']
        waiters.wait_for_volume_resource_status(
            self.admin_groups_client, grp2['id'], 'available')
        grp2_id = grp2['id']

        # Create volume
        vol1_name = data_utils.rand_name("volume")
        params = {'name': vol1_name,
                  'volume_type': volume_type['id'],
                  'group_id': grp1['id'],
                  'size': CONF.volume.volume_size}
        vol1 = self.admin_volume_client.create_volume(**params)['volume']
        self.assertEqual(grp1['id'], vol1['group_id'])
        waiters.wait_for_volume_resource_status(
            self.admin_volume_client, vol1['id'], 'available')
        vol1_id = vol1['id']

        # Get a given group
        grp1 = self.admin_groups_client.show_group(grp1['id'])['group']
        self.assertEqual(grp1_name, grp1['name'])
        self.assertEqual(grp1_id, grp1['id'])

        grp2 = self.admin_groups_client.show_group(grp2['id'])['group']
        self.assertEqual(grp2_name, grp2['name'])
        self.assertEqual(grp2_id, grp2['id'])

        # Get all groups with detail
        grps = self.admin_groups_client.list_groups(
            detail=True)['groups']
        filtered_grps = [g for g in grps if g['id'] in [grp1_id, grp2_id]]
        self.assertEqual(2, len(filtered_grps))
        for grp in filtered_grps:
            self.assertEqual([volume_type['id']], grp['volume_types'])
            self.assertEqual(group_type['id'], grp['group_type'])

        vols = self.admin_volume_client.list_volumes(
            detail=True)['volumes']
        filtered_vols = [v for v in vols if v['id'] in [vol1_id]]
        self.assertEqual(1, len(filtered_vols))
        for vol in filtered_vols:
            self.assertEqual(grp1_id, vol['group_id'])

        # Delete group
        # grp1 has a volume so delete_volumes flag is set to True by default
        self._delete_group(grp1_id)
        # grp2 is empty so delete_volumes flag can be set to False
        self._delete_group(grp2_id, delete_volumes=False)
        grps = self.admin_groups_client.list_groups(
            detail=True)['groups']
        self.assertEmpty(grps)
