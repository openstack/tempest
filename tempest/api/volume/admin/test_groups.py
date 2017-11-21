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
    min_microversion = '3.13'
    max_microversion = 'latest'

    @decorators.idempotent_id('4b111d28-b73d-4908-9bd2-03dc2992e4d4')
    def test_group_create_show_list_delete(self):
        # Create volume type
        volume_type = self.create_volume_type()

        # Create group type
        group_type = self.create_group_type()

        # Create group
        grp1_name = data_utils.rand_name('Group1')
        grp1 = self.create_group(group_type=group_type['id'],
                                 volume_types=[volume_type['id']],
                                 name=grp1_name)
        grp1_id = grp1['id']

        grp2_name = data_utils.rand_name('Group2')
        grp2 = self.create_group(group_type=group_type['id'],
                                 volume_types=[volume_type['id']],
                                 name=grp2_name)
        grp2_id = grp2['id']

        # Create volume
        vol1_name = data_utils.rand_name("volume")
        params = {'name': vol1_name,
                  'volume_type': volume_type['id'],
                  'group_id': grp1['id'],
                  'size': CONF.volume.volume_size}
        vol1 = self.volumes_client.create_volume(**params)['volume']
        self.assertEqual(grp1['id'], vol1['group_id'])
        waiters.wait_for_volume_resource_status(
            self.volumes_client, vol1['id'], 'available')
        vol1_id = vol1['id']

        # Get a given group
        grp1 = self.groups_client.show_group(grp1['id'])['group']
        self.assertEqual(grp1_name, grp1['name'])
        self.assertEqual(grp1_id, grp1['id'])

        grp2 = self.groups_client.show_group(grp2['id'])['group']
        self.assertEqual(grp2_name, grp2['name'])
        self.assertEqual(grp2_id, grp2['id'])

        # Get all groups with detail
        grps = self.groups_client.list_groups(detail=True)['groups']
        for grp_id in [grp1_id, grp2_id]:
            filtered_grps = [g for g in grps if g['id'] == grp_id]
            self.assertEqual(1, len(filtered_grps))
            self.assertEqual([volume_type['id']],
                             filtered_grps[0]['volume_types'])
            self.assertEqual(group_type['id'],
                             filtered_grps[0]['group_type'])

        vols = self.volumes_client.list_volumes(detail=True)['volumes']
        filtered_vols = [v for v in vols if v['id'] in [vol1_id]]
        self.assertEqual(1, len(filtered_vols))
        for vol in filtered_vols:
            self.assertEqual(grp1_id, vol['group_id'])

        # Delete group
        # grp1 has a volume so delete_volumes flag is set to True by default
        self.delete_group(grp1_id)
        # grp2 is empty so delete_volumes flag can be set to False
        self.delete_group(grp2_id, delete_volumes=False)
        grps = self.groups_client.list_groups(detail=True)['groups']
        self.assertEmpty(grps)

    @decorators.idempotent_id('4a8a6fd2-8b3b-4641-8f54-6a6f99320006')
    def test_group_update(self):
        # Create volume type
        volume_type = self.create_volume_type()

        # Create group type
        group_type = self.create_group_type()

        # Create Group
        grp = self.create_group(group_type=group_type['id'],
                                volume_types=[volume_type['id']])

        # Create volumes
        grp_vols = []
        for _ in range(2):
            vol = self.create_volume(volume_type=volume_type['id'],
                                     group_id=grp['id'])
            grp_vols.append(vol)
        vol2 = grp_vols[1]

        # Remove a volume from group and update name and description
        new_grp_name = 'new_group'
        new_desc = 'This is a new group'
        grp_params = {'name': new_grp_name,
                      'description': new_desc,
                      'remove_volumes': vol2['id']}
        self.groups_client.update_group(grp['id'], **grp_params)

        # Wait for group status to become available
        waiters.wait_for_volume_resource_status(
            self.groups_client, grp['id'], 'available')

        # Get the updated Group
        grp = self.groups_client.show_group(grp['id'])['group']
        self.assertEqual(new_grp_name, grp['name'])
        self.assertEqual(new_desc, grp['description'])

        # Get volumes in the group
        vols = self.volumes_client.list_volumes(detail=True)['volumes']
        grp_vols = [v for v in vols if v['group_id'] == grp['id']]
        self.assertEqual(1, len(grp_vols))

        # Add a volume to the group
        grp_params = {'add_volumes': vol2['id']}
        self.groups_client.update_group(grp['id'], **grp_params)

        # Wait for group status to become available
        waiters.wait_for_volume_resource_status(
            self.groups_client, grp['id'], 'available')

        # Get volumes in the group
        vols = self.volumes_client.list_volumes(detail=True)['volumes']
        grp_vols = [v for v in vols if v['group_id'] == grp['id']]
        self.assertEqual(2, len(grp_vols))


class GroupsV314Test(base.BaseVolumeAdminTest):
    _api_version = 3
    min_microversion = '3.14'
    max_microversion = 'latest'

    @decorators.idempotent_id('2424af8c-7851-4888-986a-794b10c3210e')
    def test_create_group_from_group(self):
        # Create volume type
        volume_type = self.create_volume_type()

        # Create group type
        group_type = self.create_group_type()

        # Create Group
        grp = self.create_group(group_type=group_type['id'],
                                volume_types=[volume_type['id']])

        # Create volume
        self.create_volume(volume_type=volume_type['id'], group_id=grp['id'])

        # Create Group from Group
        grp_name2 = data_utils.rand_name('Group_from_grp')
        grp2 = self.groups_client.create_group_from_source(
            source_group_id=grp['id'], name=grp_name2)['group']
        self.addCleanup(self.delete_group, grp2['id'])
        self.assertEqual(grp_name2, grp2['name'])
        vols = self.volumes_client.list_volumes(detail=True)['volumes']
        for vol in vols:
            if vol['group_id'] == grp2['id']:
                waiters.wait_for_volume_resource_status(
                    self.volumes_client, vol['id'], 'available')
        waiters.wait_for_volume_resource_status(
            self.groups_client, grp2['id'], 'available')


class GroupsV320Test(base.BaseVolumeAdminTest):
    _api_version = 3
    min_microversion = '3.20'
    max_microversion = 'latest'

    @decorators.idempotent_id('b20c696b-0cbc-49a5-8b3a-b1fb9338f45c')
    def test_reset_group_status(self):
        # Create volume type
        volume_type = self.create_volume_type()

        # Create group type
        group_type = self.create_group_type()

        # Create group
        group = self.create_group(group_type=group_type['id'],
                                  volume_types=[volume_type['id']])

        # Reset group status
        self.addCleanup(waiters.wait_for_volume_resource_status,
                        self.groups_client, group['id'], 'available')
        self.addCleanup(self.admin_groups_client.reset_group_status,
                        group['id'], 'available')
        for status in ['creating', 'available', 'error']:
            self.admin_groups_client.reset_group_status(group['id'], status)
            waiters.wait_for_volume_resource_status(
                self.groups_client, group['id'], status)
